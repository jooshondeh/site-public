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
BUILD = "production-2026-07-19-v6-no-tracking"
CACHE = "20260719prod6"
PHONE_HREF = "tel:+18044609640"
PHONE_TEXT = "(804) 460-9640"
GOOGLE_BUSINESS_URL = "https://share.google/UWWubeCa8CN4sffAM"

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
        self.images_without_alt = []
        self.canonicals = []
        self.robots = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        element_id = data.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicates.add(element_id)
            self.ids.add(element_id)
        classes = data.get("class", "").split()
        if "data-call-phone" in data:
            self.phones.append((tag, data.get("href"), data.get("title")))
        if tag == "span" and "phone-number-display" in classes:
            self.in_phone_display = True
            self.phone_display_texts.append("")
        if "google-business" in classes:
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

    def handle_endtag(self, tag):
        if tag == "span" and self.in_phone_display:
            self.in_phone_display = False

    def handle_data(self, data):
        if self.in_phone_display and self.phone_display_texts:
            self.phone_display_texts[-1] += data

errors = []
phone_count = 0
phone_display_count = 0
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
    GOOGLE_BUSINESS_URL,
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
for undefined in ("var(--ink)", "var(--navy)", "var(--link)"):
    if undefined in css:
        errors.append(f"CSS contains undefined token: {undefined}")

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
    if not lastmods or any(value != "2026-07-19" for value in lastmods):
        errors.append(f"Sitemap lastmod values are stale: {lastmods}")
except ET.ParseError as exc:
    errors.append(f"Invalid sitemap.xml: {exc}")

if args.clean and (ROOT / "CNAME").read_text(encoding="utf-8").strip() != "nexgenbinary.com":
    errors.append("CNAME is not configured for nexgenbinary.com")

if errors:
    raise SystemExit("\n".join(errors))

print(f"Validated {len(html_files)} HTML files, {phone_count} native phone links, no tracking code, SEO metadata, and integrations.")
