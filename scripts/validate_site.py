#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import argparse
import json
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(
    description="Validate the NexGen Binary production website."
)
parser.add_argument("root", nargs="?", default=".")
parser.add_argument("--clean", action="store_true")
args = parser.parse_args()

ROOT = Path(args.root).resolve()
PRODUCTION_ORIGIN = "https://nexgenbinary.com"
<<<<<<< HEAD
BUILD = "production-2026-07-18-v5-1-hcaptcha"
CACHE = "20260718prod51"
=======
BUILD = "production-2026-07-18-v5-audit"
CACHE = "20260718prod5"
>>>>>>> 15507804926698986b3bc4eb9d0a05112c2207c7
MEASUREMENT_ID = "G-YY6Q8RTE7R"
PHONE_HREF = "tel:+18044609640"
PHONE_TEXT = "(804) 460-9640"
GOOGLE_BUSINESS_URL = "https://share.google/UWWubeCa8CN4sffAM"

SOURCE_REQUIRED = [
    "index.html", "404.html", "robots.txt", "sitemap.xml",
    "assets/site.css", "assets/site.js", "assets/analytics.js",
    "book/index.html", "privacy/index.html", "terms/index.html",
    "nexgenbinary-logo.png", "social-preview.png",
    "favicon.ico", "favicon.svg", "favicon-16x16.png",
    "favicon-32x32.png", "favicon-192x192.png",
    "favicon-512x512.png", "apple-touch-icon.png",
]

DEPLOYMENT_ONLY_REQUIRED = [
    "CNAME", ".nojekyll", ".well-known/security.txt",
]

REQUIRED = SOURCE_REQUIRED + (DEPLOYMENT_ONLY_REQUIRED if args.clean else [])

FORBIDDEN_DEPLOYED = [
    "_astro", "docs", "scripts", ".github",
    "assets/analytics-id.js", "assets/analytics-config.js",
    "site.webmanifest",
]

missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
if missing:
    raise SystemExit(
        "Missing required website files:\n"
        + "\n".join(f"  - {item}" for item in missing)
    )

if args.clean:
    for item in FORBIDDEN_DEPLOYED:
        if (ROOT / item).exists():
            raise SystemExit(
                f"Repository-only or obsolete item entered deployment: {item}"
            )

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
        self.in_phone_display = False
        self.phone_display_texts = []

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

    for marker in (
        BUILD,
        f"site.css?v={CACHE}",
        f"site.js?v={CACHE}",
        f"analytics.js?v={CACHE}",
        f"googletagmanager.com/gtag/js?id={MEASUREMENT_ID}",
        f"const measurementId = '{MEASUREMENT_ID}'",
        "gtag('consent', 'default'",
        "send_page_view: false",
    ):
        if marker not in text:
            errors.append(f"{relative} missing build/analytics marker: {marker}")

    if "analytics-id.js" in text or "analytics-config.js" in text:
        errors.append(f"{relative} references an obsolete analytics loader")

    if "site.webmanifest" in text or 'rel="manifest"' in text:
        errors.append(f"{relative} enables an unwanted install prompt")

    if 'name="viewport"' not in text:
        errors.append(f"{relative} missing viewport metadata")

    if "nexgenbinary-stage" in text or "jooshondeh.github.io" in text:
        errors.append(f"{relative} contains staging URLs")

    if "allow=\"camera;" in text:
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
            errors.append(
                f"{relative} phone display is not real visible text: {visible_text!r}"
            )

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

    if relative in (
        Path("index.html"),
        Path("privacy/index.html"),
        Path("terms/index.html"),
    ):
        if not parsed.canonicals or not parsed.canonicals[0].startswith(
            PRODUCTION_ORIGIN
        ):
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
    "Dental IT Support",
    "&amp; Managed Services",
    "Across Virginia",
    "Future-Ready Systems. Human-Ready Support.",
    "https://formspree.io/f/mdalpbzo",
    "267e959c-42c0-45b2-a4d2-45621dbc4f28",
    "https://outlook.office.com/book/MeetNexGenBinary@nexgenbinary.com/",
    "data-booking-open", "data-back-to-top",
    '"@type": "ProfessionalService"',
    GOOGLE_BUSINESS_URL,
):
    if marker not in index:
        errors.append(f"index.html missing required marker: {marker}")

if "https://js.hcaptcha.com/1/api.js" in index:
    errors.append("index.html still loads hCaptcha during the initial page request")

<<<<<<< HEAD
for marker in (
    'data-hcaptcha-lazy',
    'data-hcaptcha-load-status',
    'class="captcha-load-status"',
    'data-sitekey="267e959c-42c0-45b2-a4d2-45621dbc4f28"',
):
    if marker not in index:
        errors.append(f"index.html missing deferred hCaptcha marker: {marker}")

=======
>>>>>>> 15507804926698986b3bc4eb9d0a05112c2207c7
if index.count('class="plan-row"') != 24:
    errors.append("index.html must contain exactly 24 service-plan rows")

privacy = (ROOT / "privacy/index.html").read_text(encoding="utf-8")
for marker in (
    "Google Analytics is configured with Consent Mode",
    "limited cookieless consent and measurement signals",
    "closing the analytics notice records a declined choice",
):
    if marker not in privacy:
        errors.append(f"privacy/index.html missing disclosure: {marker}")

analytics_js = (ROOT / "assets/analytics.js").read_text(encoding="utf-8")
for marker in (
    f"const measurementId = '{MEASUREMENT_ID}'",
    f"const storageKey = '{'nexgen_analytics_consent_v3'}'",
    "navigator.globalPrivacyControl",
    "pageViewSent",
    "data-analytics-close",
    "Close analytics preferences and decline analytics",
    "role', 'region",
    "generate_lead",
    "click_to_call",
):
    if marker not in analytics_js:
        errors.append(f"assets/analytics.js missing marker: {marker}")

site_js = (ROOT / "assets/site.js").read_text(encoding="utf-8")
for marker in (
    f"const phoneDisplayText = '{PHONE_TEXT}'",
    "const removePhoneDecorations",
    "successReturnFocus",
    "successFocusable",
<<<<<<< HEAD
    "'[data-hcaptcha-lazy], .h-captcha[data-sitekey]'",
    "nexgenHCaptchaReady",
    "render=explicit",
=======
>>>>>>> 15507804926698986b3bc4eb9d0a05112c2207c7
    "nexgen:contact-form-success",
    "nexgen:section-change",
):
    if marker not in site_js:
        errors.append(f"assets/site.js missing protected function: {marker}")

css = (ROOT / "assets/site.css").read_text(encoding="utf-8")
if 'content: "(804) 460-9640"' in css:
    errors.append("Phone number is still generated through CSS")
for undefined in ("var(--ink)", "var(--navy)", "var(--link)"):
    if undefined in css:
        errors.append(f"CSS still contains undefined token: {undefined}")

robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
if "Disallow: /" in robots:
    errors.append("Production robots.txt blocks crawling")
if f"Sitemap: {PRODUCTION_ORIGIN}/sitemap.xml" not in robots:
    errors.append("robots.txt missing production sitemap URL")

try:
    sitemap = ET.parse(ROOT / "sitemap.xml")
    locations = [
        element.text
        for element in sitemap.findall(
            ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
        )
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

if errors:
    raise SystemExit("\n".join(errors))

print(
    f"Validated {len(html_files)} HTML files, {phone_count} native phone links, "
    "direct Google Analytics consent behavior, SEO metadata, and integrations."
)
