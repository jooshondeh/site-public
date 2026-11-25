#!/usr/bin/env python3
"""Read-only release checks. Run after the GitHub Pages deployment succeeds.

This script fetches public pages/assets only. It does not submit the contact
form, solve hCaptcha, book appointments, or change any account settings.
"""
import argparse
import struct
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BUILD = "production-2026-11-25-v9-blue-brand"
CACHE = "20261125brand9"
RELEASE_DATE = "2026-11-25"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--base", default="https://nexgenbinary.com", help="Site origin to check")
parser.add_argument("--timeout", type=float, default=20, help="Seconds allowed per request")
args = parser.parse_args()
BASE = args.base.rstrip("/")
errors = []


def fetch(route, expected_status=200):
    request = Request(
        BASE + route,
        headers={
            "User-Agent": "NexGenBinaryProductionCheck/2.0",
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
