#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import argparse
import json
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description="Validate the NexGen Binary production website.")
parser.add_argument("root", nargs="?", default=".")
parser.add_argument("--clean", action="store_true")
args = parser.parse_args()

ROOT = Path(args.root).resolve()
PRODUCTION_ORIGIN = "https://nexgenbinary.com"
BUILD = "production-2026-07-18-v2"
CACHE = "20260718prod2"
PHONE_HREF = "tel:+18044609640"
GOOGLE_BUSINESS_URL = "https://share.google/UWWubeCa8CN4sffAM"

SOURCE_REQUIRED = [
    "index.html", "404.html", "robots.txt", "sitemap.xml",
    "assets/site.css", "assets/site.js",
    "assets/analytics-id.js", "assets/analytics-config.js", "assets/analytics.js",
    "book/index.html", "privacy/index.html", "terms/index.html",
    "nexgenbinary-logo.png", "social-preview.png",
    "favicon.ico", "favicon.svg", "favicon-16x16.png",
    "favicon-32x32.png", "favicon-192x192.png",
    "favicon-512x512.png", "apple-touch-icon.png",
]

DEPLOYMENT_ONLY_REQUIRED = [
    "CNAME",
    ".nojekyll",
    ".well-known/security.txt",
]

REQUIRED = SOURCE_REQUIRED + (DEPLOYMENT_ONLY_REQUIRED if args.clean else [])

FORBIDDEN_DEPLOYED = [
    "_astro", "docs", "scripts", ".github",
    "QA-REPORT.json", "SHA256SUMS.txt",
]

for item in REQUIRED:
    if not (ROOT / item).is_file():
        raise SystemExit(f"Missing required production file: {item}")

if args.clean:
    for item in FORBIDDEN_DEPLOYED:
        if (ROOT / item).exists():
            raise SystemExit(f"Repository-only item entered deployment artifact: {item}")

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = set()
        self.duplicates = set()
        self.phones = []
        self.google_links = []
        self.images_without_alt = []
        self.titles = []
        self.canonicals = []
        self.robots = []
        self.json_ld = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)

        element_id = data.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicates.add(element_id)
            self.ids.add(element_id)

        if "data-call-phone" in data:
            self.phones.append((tag, data.get("href"), data.get("title")))

        if "google-business" in data.get("class", "").split():
            self.google_links.append((tag, data.get("href")))

        if tag == "img" and "alt" not in data:
            self.images_without_alt.append(data.get("src", "<unknown>"))

        if tag == "link" and "canonical" in data.get("rel", "").split():
            self.canonicals.append(data.get("href"))

        if tag == "meta" and data.get("name") == "robots":
            self.robots.append(data.get("content"))

        for key in ("href", "src", "data-src"):
            value = data.get(key)
            if value:
                self.refs.append(value)

    def handle_data(self, data):
        pass

errors = []
phone_count = 0
titles = {}
html_files = sorted(ROOT.rglob("*.html"))

for path in html_files:
    text = path.read_text(encoding="utf-8")
    parsed = Parser()
    parsed.feed(text)
    relative = path.relative_to(ROOT)

    if parsed.duplicates:
        errors.append(f"{relative} duplicate IDs: {sorted(parsed.duplicates)}")

    if parsed.images_without_alt:
        errors.append(f"{relative} images missing alt: {parsed.images_without_alt}")

    if BUILD not in text:
        errors.append(f"{relative} missing production build marker")

    if f"site.css?v={CACHE}" not in text:
        errors.append(f"{relative} missing current CSS cache version")

    if f"site.js?v={CACHE}" not in text:
        errors.append(f"{relative} missing current JS cache version")

    if f"analytics-id.js?v={CACHE}" not in text:
        errors.append(f"{relative} missing analytics ID loader reference")

    if f"analytics-config.js?v={CACHE}" not in text:
        errors.append(f"{relative} missing analytics config reference")

    if f"analytics.js?v={CACHE}" not in text:
        errors.append(f"{relative} missing analytics loader reference")

    if 'name="viewport"' not in text:
        errors.append(f"{relative} missing viewport metadata")

    if 'rel="manifest"' in text or "site.webmanifest" in text:
        errors.append(f"{relative} still enables the browser install prompt")

    if 'name="referrer"' not in text or "strict-origin-when-cross-origin" not in text:
        errors.append(f"{relative} missing Formspree-compatible referrer policy")

    if "nexgenbinary-stage" in text or "jooshondeh.github.io" in text:
        errors.append(f"{relative} still contains staging URLs")

    if "noindex,nofollow,noarchive" in text and relative != Path("404.html"):
        errors.append(f"{relative} unexpectedly uses staging noindex directive")

    for tag, href, title in parsed.phones:
        phone_count += 1
        if tag != "a" or href != PHONE_HREF:
            errors.append(f"{relative} phone control is not a native tel link")
        if title is not None:
            errors.append(f"{relative} phone link has an unwanted tooltip title")

    if not parsed.google_links:
        errors.append(f"{relative} missing Google Business link")

    for tag, href in parsed.google_links:
        if tag != "a" or href != GOOGLE_BUSINESS_URL:
            errors.append(f"{relative} incorrect Google Business URL: {href}")

    # Resolve local references from the current file's directory.
    for ref in parsed.refs:
        if ref.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue

        parsed_url = urlparse(ref)
        if parsed_url.scheme in ("http", "https"):
            continue

        clean = unquote(parsed_url.path)
        if not clean:
            continue

        target = (path.parent / clean).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            errors.append(f"{relative} reference escapes site root: {ref}")
            continue

        if clean.endswith("/"):
            target = target / "index.html"
        elif not target.suffix and target.is_dir():
            target = target / "index.html"

        if not target.exists():
            errors.append(f"{relative} missing local reference: {ref}")

    title_start = text.find("<title>")
    title_end = text.find("</title>")
    if title_start == -1 or title_end == -1:
        errors.append(f"{relative} missing title")
    else:
        title = text[title_start + 7:title_end].strip()
        if not title:
            errors.append(f"{relative} has an empty title")
        titles.setdefault(title, []).append(str(relative))

    if relative in (Path("index.html"), Path("privacy/index.html"), Path("terms/index.html")):
        if not parsed.canonicals or not parsed.canonicals[0].startswith(PRODUCTION_ORIGIN):
            errors.append(f"{relative} missing production canonical URL")
        if not parsed.robots or not parsed.robots[0].startswith("index,follow"):
            errors.append(f"{relative} must be indexable")

    if relative == Path("book/index.html"):
        if not parsed.robots or parsed.robots[0] != "noindex,follow":
            errors.append("book/index.html must remain noindex,follow")

    if relative == Path("404.html"):
        if parsed.canonicals:
            errors.append("404.html must not declare a canonical URL")
        if not parsed.robots or "noindex" not in parsed.robots[0]:
            errors.append("404.html must be noindex")

if phone_count != 14:
    errors.append(f"Expected 14 phone links, found {phone_count}")

for title, pages in titles.items():
    if len(pages) > 1 and title != "NexGen Binary":
        errors.append(f"Duplicate page title {title!r} on {pages}")

index = (ROOT / "index.html").read_text(encoding="utf-8")

for marker in (
    "https://formspree.io/f/mdalpbzo",
    "267e959c-42c0-45b2-a4d2-45621dbc4f28",
    "https://outlook.office.com/book/MeetNexGenBinary@nexgenbinary.com/",
    "VoIP, business audio systems, and camera solutions planned for reliable coverage",
    "data-booking-open", "data-back-to-top",
    '"@type": "ProfessionalService"',
    GOOGLE_BUSINESS_URL,
):
    if marker not in index:
        errors.append(f"index.html missing required production marker: {marker}")

if index.count('class="plan-row"') != 24:
    errors.append("index.html must contain exactly 24 service-plan rows")

if '<meta content="noindex' in index:
    errors.append("Production homepage is noindex")

# Validate JSON-LD.
from html.parser import HTMLParser as _HTMLParser
class JsonLdParser(_HTMLParser):
    def __init__(self):
        super().__init__()
        self.capture = False
        self.parts = []
        self.blocks = []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "script" and data.get("type") == "application/ld+json":
            self.capture = True
            self.parts = []
    def handle_data(self, data):
        if self.capture:
            self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == "script" and self.capture:
            self.blocks.append("".join(self.parts))
            self.capture = False

json_parser = JsonLdParser()
json_parser.feed(index)
if len(json_parser.blocks) != 1:
    errors.append(f"Expected one JSON-LD block, found {len(json_parser.blocks)}")
else:
    try:
        structured = json.loads(json_parser.blocks[0])
        serialized = json.dumps(structured)
        if PRODUCTION_ORIGIN not in serialized or GOOGLE_BUSINESS_URL not in serialized:
            errors.append("JSON-LD missing production domain or Google Business URL")
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON-LD: {exc}")

# Production discovery files.
robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
if "Disallow: /" in robots:
    errors.append("Production robots.txt still blocks crawling")
if f"Sitemap: {PRODUCTION_ORIGIN}/sitemap.xml" not in robots:
    errors.append("robots.txt missing production sitemap URL")

try:
    sitemap = ET.parse(ROOT / "sitemap.xml")
    locations = [
        element.text
        for element in sitemap.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    ]
    expected = {
        f"{PRODUCTION_ORIGIN}/",
        f"{PRODUCTION_ORIGIN}/privacy/",
        f"{PRODUCTION_ORIGIN}/terms/",
    }
    if set(locations) != expected:
        errors.append(f"Unexpected sitemap URLs: {locations}")
except ET.ParseError as exc:
    errors.append(f"Invalid sitemap.xml: {exc}")

if args.clean:
    if (ROOT / "CNAME").read_text(encoding="utf-8").strip() != "nexgenbinary.com":
        errors.append("CNAME is not configured for nexgenbinary.com")

analytics_id = (ROOT / "assets/analytics-id.js").read_text(encoding="utf-8")
analytics_config = (ROOT / "assets/analytics-config.js").read_text(encoding="utf-8")
if "NEXGEN_GA4_MEASUREMENT_ID" not in analytics_id or "NEXGEN_GA4_MEASUREMENT_ID" not in analytics_config:
    errors.append("Analytics ID injection configuration is missing")
if "G-XXXXXXXX" in analytics_id or "G-XXXXXXXX" in analytics_config:
    errors.append("Analytics files contain a fake placeholder ID")

site_js = (ROOT / "assets/site.js").read_text(encoding="utf-8")
for marker in (
    "const removePhoneDecorations",
    "element.tagName === 'svg' || element === display",
    "scrollReloadToTop",
    "nexgen:contact-form-success",
    "nexgen:section-change",
):
    if marker not in site_js:
        errors.append(f"assets/site.js missing protected functionality: {marker}")

if errors:
    raise SystemExit("\n".join(errors))

print(f"Validated {len(html_files)} HTML files, {phone_count} phone links, SEO discovery files, and production integrations in {ROOT}")
