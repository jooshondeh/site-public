#!/usr/bin/env python3
"""Read-only release checks. Run after the GitHub Pages deployment succeeds.

This script fetches public pages/assets only. It does not submit the contact
form, solve hCaptcha, book appointments, or change any account settings.
"""
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import re
import struct
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BUILD = "production-2026-11-25-v11-service-plans"
CACHE = "20261125plans11"
RELEASE_DATE = "2026-11-25"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--base", default="https://nexgenbinary.com", help="Site origin to check")
parser.add_argument("--timeout", type=float, default=20, help="Seconds allowed per request")
args = parser.parse_args()
BASE = args.base.rstrip("/")
errors = []


class ReleaseParser(HTMLParser):
    """Collect release landmarks without relying on attribute order or quoting."""
    def __init__(self):
        super().__init__()
        self.elements = []
        self.text = []
        self.skip_text = None
        self.in_interest = False
        self.interest_options = []
        self.sections = []
        self.faq_disclosures = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if tag in ("script", "style", "svg"):
            self.skip_text = tag
        if tag == "section":
            self.sections.append(attrs.get("id"))
        if tag == "details" and "coverage-questions" in self.sections:
            self.faq_disclosures += 1
        if tag == "select" and attrs.get("id") == "contact-interest":
            self.in_interest = True
        if tag == "option" and self.in_interest:
            self.interest_options.append(attrs.get("value"))

    def handle_endtag(self, tag):
        if tag == self.skip_text:
            self.skip_text = None
        if tag == "select":
            self.in_interest = False
        if tag == "section" and self.sections:
            self.sections.pop()

    def handle_data(self, data):
        if self.skip_text is None:
            self.text.append(data)


def check_homepage_structure(body):
    parsed = ReleaseParser()
    parsed.feed(body)
    parsed.close()
    names = {"essentials": "Managed IT Essentials", "standard": "Managed IT Standard", "premium": "Managed IT Premium"}
    cards = [attrs for tag, attrs in parsed.elements if tag == "article" and "plan-summary" in attrs.get("class", "").split()]
    if len(cards) != 3 or sorted(card.get("data-plan", "") for card in cards) != sorted(names):
        errors.append("/: expected the three v11 managed-plan summaries")
    recommended = [card for card in cards if card.get("data-recommended") == "true"]
    if len(recommended) != 1 or recommended[0].get("data-plan") != "standard":
        errors.append("/: Standard must be the only recommended plan")
    readable = " ".join(" ".join(parsed.text).split())
    for name in names.values():
        if name not in readable:
            errors.append(f"/: missing readable plan name {name!r}")
    for tag, element_id in (("div", "plan-comparison"), ("table", "plan-comparison-table"), ("section", "additional-services"), ("section", "coverage-questions"), ("select", "contact-interest")):
        matches = [attrs for candidate, attrs in parsed.elements if candidate == tag and attrs.get("id") == element_id]
        if len(matches) != 1:
            errors.append(f"/: expected one {tag} #{element_id}")
        elif element_id == "plan-comparison" and "plan-comparison-content" not in matches[0].get("class", "").split():
            errors.append("/: comparison anchor must be on the shared plan-comparison-content wrapper")
        elif tag == "select" and matches[0].get("name") != "interest":
            errors.append("/: contact-interest must submit under the interest field")
    features = {"remote-support", "maintenance", "endpoint-protection", "monitoring-alerts", "backup-management", "restore-testing", "backup-reporting", "vendor-coordination", "onsite-maintenance", "technology-planning", "warranty-coordination", "loaner-equipment", "after-hours"}
    rows = [attrs.get("data-feature") for tag, attrs in parsed.elements if tag == "tr" and "data-feature" in attrs]
    if len(rows) != 13 or set(rows) != features:
        errors.append("/: comparison must expose all 13 distinct service features")
    quote_links = [attrs for tag, attrs in parsed.elements if tag == "a" and "data-plan-select" in attrs]
    if len(quote_links) != 6:
        errors.append("/: expected six plan-specific quote links")
    for name in names.values():
        matching = [attrs for attrs in quote_links if attrs.get("data-plan-select") == name]
        if len(matching) != 2 or any(attrs.get("href") != "#contact-form" for attrs in matching):
            errors.append(f"/: incorrect quote routing for {name}")
    expected_options = set(names.values()) | {"Help me choose", "Project or one-time support"}
    if set(parsed.interest_options) - {""} != expected_options or len(parsed.interest_options) != len(set(parsed.interest_options)):
        errors.append("/: contact interest choices do not match the current plans")
    if not parsed.faq_disclosures:
        errors.append("/: coverage questions require native details disclosures")
    if "Managed IT Complete" in readable or re.search(r"[$£€]\s*\d|\bUSD\s*\d", readable):
        errors.append("/: obsolete plan wording or numeric public pricing is still deployed")


def fetch(route, expected_status=200):
    request = Request(
        BASE + route,
        headers={
            "User-Agent": "NexGenBinaryProductionCheck/3.0",
            "Cache-Control": "no-cache",
        },
    )
    try:
        try:
            response = urlopen(request, timeout=args.timeout)
        except HTTPError as exc:
            response = exc  # An intentional missing route must return the custom 404.
        with response:
            status = response.code
            body = response.read(5 * 1024 * 1024)
        if status != expected_status:
            errors.append(f"{route}: HTTP {status}; expected {expected_status}")
            return None
        return body
    except (URLError, TimeoutError, OSError) as exc:
        errors.append(f"{route}: could not retrieve the page: {exc}")
        return None


common_page_markers = [
    BUILD,
    f"assets/site.css?v={CACHE}",
    f"assets/site.js?v={CACHE}",
    f"nexgenbinary-logo.png?v={CACHE}",
    "(804) 460-9640",
    "https://www.facebook.com/NexGenBinary/",
]
checks = {
    "/": common_page_markers + [
        "Dental IT Support &amp; Managed Services in Virginia | NexGen Binary",
        "data-hcaptcha-lazy",
        "Monday–Saturday, 8:00 AM–5:00 PM Eastern Time",
    ],
    "/book/": common_page_markers + ["noindex,follow", "outlook.office.com/book/"],
    "/privacy/": common_page_markers + ["Cookies and Browser Storage"],
    "/terms/": common_page_markers + ["Terms of Use"],
    "/404.html": common_page_markers + ["noindex"],
    "/robots.txt": ["Sitemap: https://nexgenbinary.com/sitemap.xml"],
    "/sitemap.xml": ["https://nexgenbinary.com/", RELEASE_DATE],
    "/.well-known/security.txt": [
        "Contact: mailto:info@nexgenbinary.com",
        "Canonical: https://nexgenbinary.com/.well-known/security.txt",
    ],
}
for route, markers in checks.items():
    data = fetch(route)
    if data is None:
        if route == "/":
            raise SystemExit("Live check could not start:\n" + "\n".join(errors))
        continue
    body = data.decode("utf-8", errors="replace")
    previous_errors = len(errors)
    for marker in markers:
        if marker not in body:
            errors.append(f"{route}: missing {marker!r}")
    lowered = body.lower()
    for forbidden in ("googletagmanager", "google-analytics", "assets/analytics.js", "analytics settings"):
        if forbidden in lowered:
            errors.append(f"{route}: contains removed tracking content: {forbidden}")
    if route == "/":
        check_homepage_structure(body)
    if route == "/.well-known/security.txt":
        fields = dict(line.split(": ", 1) for line in body.splitlines() if ": " in line and not line.startswith("#"))
        try:
            expiry = datetime.fromisoformat(fields.get("Expires", "").replace("Z", "+00:00"))
            if expiry.tzinfo is None or expiry <= datetime.now(timezone.utc):
                errors.append(f"{route}: Expires must be a future timestamp with a timezone")
        except ValueError:
            errors.append(f"{route}: missing or invalid Expires timestamp")
    if len(errors) == previous_errors:
        print(f"OK {route}")

for asset in (
    "assets/site.css", "assets/site.js", "nexgenbinary-logo.png", "social-preview.png",
    "favicon.ico", "favicon.svg", "favicon-16x16.png", "favicon-32x32.png",
    "favicon-192x192.png", "favicon-512x512.png", "apple-touch-icon.png",
):
    data = fetch(f"/{asset}?v={CACHE}")
    if data is None:
        continue
    previous_errors = len(errors)
    if not data:
        errors.append(f"/{asset}: the deployed asset is empty")
    if asset in ("nexgenbinary-logo.png", "social-preview.png"):
        expected = (960, 396) if asset == "nexgenbinary-logo.png" else (1200, 630)
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
            errors.append(f"/{asset}: not a valid PNG header")
        elif struct.unpack(">II", data[16:24]) != expected:
            errors.append(f"/{asset}: dimensions differ from the release asset {expected}")
    elif asset == "assets/site.css":
        css = data.decode("utf-8", errors="replace").lower()
        if any(color in css for color in ("#ff8f02", "#ff9e24", "#d87300")):
            errors.append("/assets/site.css: obsolete orange branding is still deployed")
    if len(errors) == previous_errors:
        print(f"OK /{asset}")

missing_route = "/__ngb_release_check__/missing-page/"
data = fetch(missing_route, expected_status=404)
if data is not None:
    body = data.decode("utf-8", errors="replace")
    previous_errors = len(errors)
    for marker in (BUILD, "noindex", f'/assets/site.css?v={CACHE}', f'/nexgenbinary-logo.png?v={CACHE}'):
        if marker not in body:
            errors.append(f"Custom 404: missing {marker!r}")
    if len(errors) == previous_errors:
        print("OK nested missing URL returns the updated custom 404 with root-relative assets")

if errors:
    raise SystemExit(
        "Live release checks failed:\n" + "\n".join(f"  - {error}" for error in errors)
        + "\nConfirm the deployment succeeded, then allow caches to refresh and retry."
    )
print(
    "Live release checks passed. Contact-form delivery, hCaptcha verification, "
    "and completed Microsoft Bookings appointments still require manual checks."
)
