#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import argparse
import json
import re
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description="Validate the NexGen Binary production website.")
parser.add_argument("root", nargs="?", default=".")
parser.add_argument("--clean", action="store_true")
args = parser.parse_args()

ROOT = Path(args.root).resolve()
PRODUCTION_ORIGIN = "https://nexgenbinary.com"
BUILD = "production-2026-07-18-v3"
CACHE = "20260718prod3"
PHONE_HREF = "tel:+18044609640"
GOOGLE_BUSINESS_URL = "https://share.google/UWWubeCa8CN4sffAM"
HCAPTCHA_SITEKEY = "267e959c-42c0-45b2-a4d2-45621dbc4f28"

SOURCE_REQUIRED = [
    "index.html", "404.html", "robots.txt", "sitemap.xml",
    "assets/site.css", "assets/site.js",
    "assets/analytics-config.js", "assets/analytics.js",
    "book/index.html", "privacy/index.html", "terms/index.html",
    "nexgenbinary-logo.png", "social-preview.png",
    "favicon.ico", "favicon.svg", "favicon-16x16.png",
    "favicon-32x32.png", "favicon-192x192.png",
    "favicon-512x512.png", "apple-touch-icon.png",
]
DEPLOYMENT_ONLY_REQUIRED = ["CNAME", ".nojekyll", ".well-known/security.txt"]
REQUIRED = SOURCE_REQUIRED + (DEPLOYMENT_ONLY_REQUIRED if args.clean else [])
FORBIDDEN_DEPLOYED = [
    "docs", "scripts", ".github", "README.md", "SHA256SUMS.txt",
    "assets/analytics-id.js", "site.webmanifest", "_astro",
]

missing_required = [
    item for item in REQUIRED
    if not (ROOT / item).is_file()
]
if missing_required:
    formatted = "\n".join(f"  - {item}" for item in missing_required)
    raise SystemExit(
        "Missing required website files:\n"
        + formatted
        + "\n\nFor assets/analytics-config.js, use the corrected workflow. "
          "It generates that file before source validation."
    )

if args.clean:
    for item in FORBIDDEN_DEPLOYED:
        if (ROOT / item).exists():
            raise SystemExit(f"Repository-only or obsolete item entered deployment artifact: {item}")

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = set()
        self.duplicates = set()
        self.phones = []
        self.google_links = []
        self.images_without_alt = []
        self.canonicals = []
        self.robots = []
        self.scripts = []
        self.iframes = []

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
        if tag == "script" and data.get("src"):
            self.scripts.append(data.get("src"))
        if tag == "iframe":
            self.iframes.append(data)
        for key in ("href", "src", "data-src"):
            value = data.get(key)
            if value:
                self.refs.append(value)

errors = []
phone_count = 0
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
        errors.append(f"{relative} missing build marker")
    if f"site.css?v={CACHE}" not in text or f"site.js?v={CACHE}" not in text:
        errors.append(f"{relative} missing current site cache version")
    if f"analytics-config.js?v={CACHE}" not in text:
        errors.append(f"{relative} missing analytics configuration loader")
    if "analytics-id.js" in text or 'src="./assets/analytics.js' in text or 'src="../assets/analytics.js' in text:
        errors.append(f"{relative} contains obsolete direct analytics scripts")
    if 'rel="manifest"' in text or "site.webmanifest" in text:
        errors.append(f"{relative} still contains installable web-app metadata")
    if 'name="viewport"' not in text:
        errors.append(f"{relative} missing viewport metadata")
    if "nexgenbinary-stage" in text or "jooshondeh.github.io" in text:
        errors.append(f"{relative} still contains staging URLs")

    for tag, href, title in parsed.phones:
        phone_count += 1
        if tag != "a" or href != PHONE_HREF:
            errors.append(f"{relative} phone control is not a native tel link")
        if title is not None:
            errors.append(f"{relative} phone link has an unwanted tooltip")

    if not parsed.google_links:
        errors.append(f"{relative} missing Google Business link")
    for tag, href in parsed.google_links:
        if tag != "a" or href != GOOGLE_BUSINESS_URL:
            errors.append(f"{relative} incorrect Google Business URL: {href}")

    for iframe in parsed.iframes:
        source = iframe.get("src") or iframe.get("data-src") or ""
        if "outlook.office.com/book/" in source and iframe.get("allow"):
            errors.append(f"{relative} booking iframe requests unnecessary device permissions")

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

    if relative in (Path("index.html"), Path("privacy/index.html"), Path("terms/index.html")):
        if not parsed.canonicals or not parsed.canonicals[0].startswith(PRODUCTION_ORIGIN):
            errors.append(f"{relative} missing production canonical")
        if not parsed.robots or not parsed.robots[0].startswith("index,follow"):
            errors.append(f"{relative} must be indexable")
    if relative == Path("book/index.html") and (not parsed.robots or parsed.robots[0] != "noindex,follow"):
        errors.append("book/index.html must remain noindex,follow")
    if relative == Path("404.html") and (not parsed.robots or "noindex" not in parsed.robots[0]):
        errors.append("404.html must be noindex")

if phone_count != 14:
    errors.append(f"Expected 14 phone links, found {phone_count}")

index = (ROOT / "index.html").read_text(encoding="utf-8")
for marker in (
    "https://formspree.io/f/mdalpbzo",
    HCAPTCHA_SITEKEY,
    "data-hcaptcha-lazy",
    "https://outlook.office.com/book/MeetNexGenBinary@nexgenbinary.com/",
    "VoIP, business audio systems, and camera solutions planned for reliable coverage",
    "data-booking-open", "data-back-to-top",
    '"@type": "ProfessionalService"',
    GOOGLE_BUSINESS_URL,
):
    if marker not in index:
        errors.append(f"index.html missing marker: {marker}")
if "https://js.hcaptcha.com/1/api.js" in index:
    errors.append("Homepage loads hCaptcha eagerly instead of using the lazy loader")
if index.count('class="plan-row"') != 24:
    errors.append("index.html must contain exactly 24 service-plan rows")

site_js = (ROOT / "assets/site.js").read_text(encoding="utf-8")
for marker in (
    "const removePhoneDecorations",
    "element.tagName === 'svg' || element === display",
    "scrollReloadToTop",
    "const loadHCaptcha",
    "render=explicit&recaptchacompat=off",
    "rootMargin: '650px 0px'",
    "const warmExternalOrigin",
    "nexgen:contact-form-success",
):
    if marker not in site_js:
        errors.append(f"assets/site.js missing functionality: {marker}")

analytics_config = (ROOT / "assets/analytics-config.js").read_text(encoding="utf-8")
analytics_loader = (ROOT / "assets/analytics.js").read_text(encoding="utf-8")
if "NEXGEN_ANALYTICS_CONFIG" not in analytics_config or "analytics.js" not in analytics_config:
    errors.append("Analytics configuration is incomplete")
if "requestIdleCallback" not in analytics_config:
    errors.append("Analytics loader is not deferred to browser idle time")
if "generate_lead" not in analytics_loader or "click_to_call" not in analytics_loader:
    errors.append("Analytics event tracking is incomplete")
if "G-XXXXXXXX" in analytics_config or "G-YOUR" in analytics_config:
    errors.append("Analytics configuration contains a fake Measurement ID")

robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
if "Disallow: /" in robots or f"Sitemap: {PRODUCTION_ORIGIN}/sitemap.xml" not in robots:
    errors.append("robots.txt is not production-ready")
try:
    ET.parse(ROOT / "sitemap.xml")
except ET.ParseError as exc:
    errors.append(f"Invalid sitemap.xml: {exc}")

if args.clean:
    if (ROOT / "CNAME").read_text(encoding="utf-8").strip() != "nexgenbinary.com":
        errors.append("CNAME is not configured for nexgenbinary.com")
    if not (ROOT / ".nojekyll").is_file() or not (ROOT / ".well-known/security.txt").is_file():
        errors.append("Hidden deployment files are missing")

if errors:
    raise SystemExit("\n".join(errors))

print(f"Validated {len(html_files)} HTML files, {phone_count} phone links, lazy third-party loading, analytics configuration, SEO files, and production integrations in {ROOT}")
