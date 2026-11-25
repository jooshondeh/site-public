#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote, parse_qs
import argparse
import json
import re
import struct
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description="Validate the NexGen Binary production website.")
parser.add_argument("root", nargs="?", default=".")
parser.add_argument("--clean", action="store_true")
args = parser.parse_args()

ROOT = Path(args.root).resolve()
PRODUCTION_ORIGIN = "https://nexgenbinary.com"
BUILD = "production-2026-11-25-v9-blue-brand"
CACHE = "20261125brand9"
RELEASE_DATE = "2026-11-25"
PHONE_HREF = "tel:+18044609640"
PHONE_TEXT = "(804) 460-9640"
GOOGLE_BUSINESS_URL = "https://share.google/UWWubeCa8CN4sffAM"
LINKEDIN_URL = "https://www.linkedin.com/company/-nexgen-binary/"
FACEBOOK_URL = "https://www.facebook.com/NexGenBinary/"

SOURCE_REQUIRED = [
    "index.html", "404.html", "robots.txt", "sitemap.xml",
    "assets/site.css", "assets/site.js",
    "book/index.html", "privacy/index.html", "terms/index.html",
    "nexgenbinary-logo.png", "social-preview.png",
    "favicon.ico", "favicon.svg", "favicon-16x16.png",
    "favicon-32x32.png", "favicon-192x192.png",
    "favicon-512x512.png", "apple-touch-icon.png",
]
DEPLOYMENT_ONLY_REQUIRED = ["CNAME", ".nojekyll", ".well-known/security.txt"]
REQUIRED = SOURCE_REQUIRED + (DEPLOYMENT_ONLY_REQUIRED if args.clean else [])
FORBIDDEN_DEPLOYED = [
    "_astro", "docs", "scripts", ".github", "site.webmanifest",
    "assets/analytics.js", "assets/analytics-id.js", "assets/analytics-config.js",
]

missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
if missing:
    raise SystemExit("Missing required website files:\n" + "\n".join(f"  - {item}" for item in missing))

if args.clean:
    for item in FORBIDDEN_DEPLOYED:
        if (ROOT / item).exists():
            raise SystemExit(f"Repository-only or obsolete item entered deployment: {item}")

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = set()
        self.duplicates = set()
        self.phones = []
        self.phone_display_texts = []
        self.in_phone_display = False
        self.google_links = []
        self.linkedin_links = []
        self.facebook_links = []
        self.images_without_alt = []
        self.canonicals = []
        self.robots = []
        self.aria_refs = []
        self.logo_images = []
        self.json_ld = []
        self.in_json_ld = False

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        element_id = data.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicates.add(element_id)
            self.ids.add(element_id)
        classes = data.get("class", "").split()
        for attribute in (
            "aria-labelledby", "aria-describedby", "aria-controls", "aria-owns",
            "aria-activedescendant", "aria-details", "aria-errormessage", "aria-flowto",
        ):
            for referenced_id in data.get(attribute, "").split():
                self.aria_refs.append((attribute, referenced_id, element_id or tag))
        if "data-call-phone" in data:
            self.phones.append((tag, data.get("href"), data.get("title")))
        if tag == "span" and "phone-number-display" in classes:
            self.in_phone_display = True
            self.phone_display_texts.append("")
        if "google-business" in classes:
            self.google_links.append((tag, data.get("href")))
        if "linkedin-business" in classes:
            self.linkedin_links.append((tag, data.get("href")))
        if "facebook-business" in classes:
            self.facebook_links.append((tag, data.get("href")))
        if tag == "img" and "alt" not in data:
            self.images_without_alt.append(data.get("src", "<unknown>"))
        if tag == "img" and Path(urlparse(data.get("src", "")).path).name == "nexgenbinary-logo.png":
            self.logo_images.append(data)
        if tag == "link" and "canonical" in data.get("rel", "").split():
            self.canonicals.append(data.get("href"))
        if tag == "meta" and data.get("name") == "robots":
            self.robots.append(data.get("content"))
        if tag == "meta" and (
            data.get("property") in ("og:image", "og:image:secure_url")
            or data.get("name") == "twitter:image"
        ) and data.get("content"):
            self.refs.append(data["content"])
        if tag == "script" and data.get("type") == "application/ld+json":
            self.in_json_ld = True
            self.json_ld.append("")
        for key in ("href", "src", "data-src"):
            value = data.get(key)
            if value:
                self.refs.append(value)

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_json_ld = False
        if tag == "span" and self.in_phone_display:
            self.in_phone_display = False

    def handle_data(self, data):
        if self.in_phone_display and self.phone_display_texts:
            self.phone_display_texts[-1] += data
        if self.in_json_ld:
            self.json_ld[-1] += data


def local_target(source_path, ref):
    """Resolve page/root-relative URLs against the site, never the OS root."""
    url = urlparse(ref)
    if url.scheme and url.scheme not in ("http", "https"):
        return None
    if url.netloc and url.netloc != urlparse(PRODUCTION_ORIGIN).netloc:
        return None
    clean = unquote(url.path)
    if not clean:
        target = source_path
    elif clean.startswith("/") or url.netloc:
        target = ROOT / clean.lstrip("/")
    else:
        target = source_path.parent / clean
    target = target.resolve()
    target.relative_to(ROOT)  # Raise ValueError for a reference outside the site.
    if clean.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target


def png_dimensions(path):
    """Read the PNG IHDR dimensions without requiring an image library."""
    with path.open("rb") as image:
        header = image.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"{path.name} is not a PNG with a valid IHDR header")
    return struct.unpack(">II", header[16:24])


def structured_logo_objects(value):
    if isinstance(value, dict):
        if "logo" in value:
            yield value["logo"]
        for child in value.values():
            yield from structured_logo_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from structured_logo_objects(child)

errors = []
phone_count = 0
phone_display_count = 0
logo_count = 0
anchor_count = 0
aria_count = 0
try:
    logo_dimensions = png_dimensions(ROOT / "nexgenbinary-logo.png")
    if logo_dimensions != (960, 396):
        errors.append(f"Updated logo must be 960 x 396 pixels; found {logo_dimensions}")
except ValueError as exc:
    errors.append(str(exc))
    logo_dimensions = None

versioned_assets = {
    "site.css", "site.js", "nexgenbinary-logo.png", "social-preview.png",
    "favicon.ico", "favicon.svg", "favicon-16x16.png", "favicon-32x32.png",
    "favicon-192x192.png", "favicon-512x512.png", "apple-touch-icon.png",
}
html_files = sorted(
    path for path in ROOT.rglob("*.html")
    if not any(part in ("_site", ".git") for part in path.relative_to(ROOT).parts)
)
documents = {}
for path in html_files:
    parsed = Parser()
    parsed.feed(path.read_text(encoding="utf-8"))
    parsed.close()
    documents[path] = parsed

for path in html_files:
    text = path.read_text(encoding="utf-8")
    parsed = documents[path]
    relative = path.relative_to(ROOT)

    if parsed.duplicates:
        errors.append(f"{relative} duplicate IDs: {sorted(parsed.duplicates)}")
    if parsed.images_without_alt:
        errors.append(f"{relative} images missing alt: {parsed.images_without_alt}")
    for attribute, referenced_id, owner in parsed.aria_refs:
        aria_count += 1
        if referenced_id not in parsed.ids:
            errors.append(f"{relative} {owner}: {attribute} references missing ID {referenced_id!r}")
    if not parsed.logo_images:
        errors.append(f"{relative} missing the shared updated logo")
    for logo in parsed.logo_images:
        logo_count += 1
        try:
            declared = (int(logo.get("width", "")), int(logo.get("height", "")))
        except ValueError:
            declared = None
        if declared != logo_dimensions:
            errors.append(f"{relative} logo width/height {declared} do not match PNG {logo_dimensions}")
    structured_logos = []
    for raw_json in parsed.json_ld:
        try:
            structured_logos.extend(structured_logo_objects(json.loads(raw_json)))
        except json.JSONDecodeError as exc:
            errors.append(f"{relative} invalid JSON-LD: {exc}")
    if relative == Path("index.html") and not structured_logos:
        errors.append("index.html missing structured-data logo")
    for logo in structured_logos:
        if not isinstance(logo, dict):
            errors.append(f"{relative} structured-data logo must declare its URL and dimensions")
            continue
        if (logo.get("width"), logo.get("height")) != logo_dimensions:
            errors.append(f"{relative} JSON-LD logo dimensions do not match PNG {logo_dimensions}")
        if urlparse(logo.get("url", "")).path != "/nexgenbinary-logo.png":
            errors.append(f"{relative} JSON-LD logo URL does not point to the shared logo")

    for marker in (BUILD, f"site.css?v={CACHE}", f"site.js?v={CACHE}"):
        if marker not in text:
            errors.append(f"{relative} missing build/cache marker: {marker}")

    forbidden_text = (
        "googletagmanager", "google-analytics", "gtag(", "window.dataLayer",
        "data-nexgen-google-tag", "data-nexgen-gtag-source",
        "assets/analytics.js", "analytics settings", "analytics preferences",
    )
    lowered = text.lower()
    for marker in forbidden_text:
        if marker.lower() in lowered:
            errors.append(f"{relative} still contains removed tracking code/text: {marker}")

    if "site.webmanifest" in text or 'rel="manifest"' in text:
        errors.append(f"{relative} enables an unwanted install prompt")
    if 'name="viewport"' not in text:
        errors.append(f"{relative} missing viewport metadata")
    if "nexgenbinary-stage" in text or "jooshondeh.github.io" in text:
        errors.append(f"{relative} contains staging URLs")
    if 'allow="camera;' in text:
        errors.append(f"{relative} grants unnecessary booking iframe permissions")

    for tag, href, title in parsed.phones:
        phone_count += 1
        if tag != "a" or href != PHONE_HREF:
            errors.append(f"{relative} phone control is not a native tel link")
        if title is not None:
            errors.append(f"{relative} phone link has an unwanted title tooltip")
    for visible_text in parsed.phone_display_texts:
        phone_display_count += 1
        if visible_text.strip() != PHONE_TEXT:
            errors.append(f"{relative} phone display is not real visible text: {visible_text!r}")

    if not parsed.google_links:
        errors.append(f"{relative} missing Google Business link")
    for tag, href in parsed.google_links:
        if tag != "a" or href != GOOGLE_BUSINESS_URL:
            errors.append(f"{relative} incorrect Google Business URL: {href}")
    if not parsed.linkedin_links:
        errors.append(f"{relative} missing LinkedIn link")
    for tag, href in parsed.linkedin_links:
        if tag != "a" or href != LINKEDIN_URL:
            errors.append(f"{relative} incorrect LinkedIn URL: {href}")
    if not parsed.facebook_links:
        errors.append(f"{relative} missing Facebook link")
    for tag, href in parsed.facebook_links:
        if tag != "a" or href != FACEBOOK_URL:
            errors.append(f"{relative} incorrect Facebook URL: {href}")

    for ref in parsed.refs:
        parsed_url = urlparse(ref)
        try:
            target = local_target(path, ref)
        except ValueError:
            errors.append(f"{relative} reference escapes site root: {ref}")
            continue
        if target is None:
            continue
        if not target.is_file():
            errors.append(f"{relative} missing local reference: {ref}")
            continue
        if target.name in versioned_assets and parse_qs(parsed_url.query).get("v") != [CACHE]:
            errors.append(f"{relative} stale or missing asset version: {ref}; expected v={CACHE}")
        fragment = unquote(parsed_url.fragment).split(":~:", 1)[0]
        if fragment and target.suffix.lower() == ".html":
            anchor_count += 1
            target_document = documents.get(target)
            if target_document is None or fragment not in target_document.ids:
                errors.append(f"{relative} missing local anchor: {ref}")

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
if phone_display_count != 14:
    errors.append(f"Expected 14 visible phone-number spans, found {phone_display_count}")

index = (ROOT / "index.html").read_text(encoding="utf-8")
for marker in (
    "<title>Dental IT Support &amp; Managed Services in Virginia | NexGen Binary</title>",
    "Dental IT Support", "&amp; Managed Services", "Across Virginia",
    "Future-Ready Systems. Human-Ready Support.",
    "https://formspree.io/f/mdalpbzo", "267e959c-42c0-45b2-a4d2-45621dbc4f28",
    "https://outlook.office.com/book/MeetNexGenBinary@nexgenbinary.com/",
    "data-booking-open", "data-back-to-top", '"@type": "ProfessionalService"',
    GOOGLE_BUSINESS_URL, LINKEDIN_URL, FACEBOOK_URL,
    '"opens": "08:00"',
    "Monday–Saturday, 8:00 AM–5:00 PM Eastern Time",
):
    if marker not in index:
        errors.append(f"index.html missing required marker: {marker}")
if "https://js.hcaptcha.com/1/api.js" in index:
    errors.append("index.html still loads hCaptcha during the initial page request")
for marker in ('data-hcaptcha-lazy', 'data-hcaptcha-load-status', 'role="status"', 'aria-live="polite"'):
    if marker not in index:
        errors.append(f"index.html missing deferred verification marker: {marker}")
if index.count('class="plan-row"') != 24:
    errors.append("index.html must contain exactly 24 service-plan rows")

privacy = (ROOT / "privacy/index.html").read_text(encoding="utf-8")
for marker in (
    "Cookies and Browser Storage",
    "does not use advertising pixels or behavioral tracking",
    "Formspree for contact-form processing",
    "hCaptcha for spam prevention",
    "Microsoft Bookings for consultation scheduling",
):
    if marker not in privacy:
        errors.append(f"privacy/index.html missing current disclosure: {marker}")

site_js = (ROOT / "assets/site.js").read_text(encoding="utf-8")
for marker in (
    f"const phoneDisplayText = '{PHONE_TEXT}'", "const removePhoneDecorations",
    "successReturnFocus", "successFocusable",
    "'[data-hcaptcha-lazy], .h-captcha[data-sitekey]'",
    "warmExternalOrigin('https://js.hcaptcha.com')",
    "nexgenHCaptchaReady", "render=explicit",
):
    if marker not in site_js:
        errors.append(f"assets/site.js missing protected function: {marker}")

css = (ROOT / "assets/site.css").read_text(encoding="utf-8")
if 'content: "(804) 460-9640"' in css:
    errors.append("Phone number is still generated through CSS")
for marker in (".analytics-consent", ".footer-settings-link"):
    if marker in css:
        errors.append(f"CSS still contains removed preference control: {marker}")
for marker in ("justify-items: start;", "text-align: left;", ".h-captcha[data-hcaptcha-lazy] > *"):
    if marker not in css:
        errors.append(f"hCaptcha left-alignment CSS missing marker: {marker}")
css_without_comments = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
defined_variables = set(re.findall(r"(--[\w-]+)\s*:", css_without_comments))
for variable, delimiter in re.findall(r"var\(\s*(--[\w-]+)\s*([,)])", css_without_comments):
    if variable not in defined_variables and delimiter != ",":
        errors.append(f"CSS uses an undefined custom property without a fallback: {variable}")
old_brand_hex = {
    "ff8f02", "ff9e24", "d87300", "fff7e8", "f1c27a", "6d3a00",
    "5f4a24", "e7c07a", "fff8eb", "7d4d0b", "9b5d08",
}
for color in sorted(set(re.findall(r"#([0-9a-fA-F]{6})\b", css_without_comments))):
    if color.lower() in old_brand_hex:
        errors.append(f"CSS still uses an obsolete orange/warm brand color: #{color}")
if re.search(r"rgba?\(\s*255\s*,\s*143\s*,\s*2\s*[,)]", css_without_comments):
    errors.append("CSS still uses the obsolete orange RGB brand color")

robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
if "Disallow: /" in robots:
    errors.append("Production robots.txt blocks crawling")
if f"Sitemap: {PRODUCTION_ORIGIN}/sitemap.xml" not in robots:
    errors.append("robots.txt missing production sitemap URL")

try:
    sitemap = ET.parse(ROOT / "sitemap.xml")
    locations = [e.text for e in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    expected = {f"{PRODUCTION_ORIGIN}/", f"{PRODUCTION_ORIGIN}/privacy/", f"{PRODUCTION_ORIGIN}/terms/"}
    if set(locations) != expected:
        errors.append(f"Unexpected sitemap URLs: {locations}")
    lastmods = [e.text for e in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')]
    if len(lastmods) != len(expected) or any(value != RELEASE_DATE for value in lastmods):
        errors.append(f"Sitemap lastmod values are stale: {lastmods}")
except ET.ParseError as exc:
    errors.append(f"Invalid sitemap.xml: {exc}")

if args.clean and (ROOT / "CNAME").read_text(encoding="utf-8").strip() != "nexgenbinary.com":
    errors.append("CNAME is not configured for nexgenbinary.com")

if errors:
    raise SystemExit("\n".join(errors))

print(
    f"Validated {len(html_files)} HTML files, {phone_count} native phone links, "
    f"{logo_count} updated logos, {anchor_count} local anchors, {aria_count} ARIA references, "
    "asset versions, CSS custom properties, blue branding, business hours, social links, "
    "no tracking code, SEO metadata, and integration hooks. "
    "Static checks do not verify external form delivery or bookings."
)
