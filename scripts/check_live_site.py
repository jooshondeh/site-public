#!/usr/bin/env python3
from urllib.request import Request, urlopen

BASE = "https://nexgenbinary.com"
checks = {
    "/": [
        "Dental IT Support &amp; Managed Services in Virginia | NexGen Binary",
        "data-hcaptcha-lazy",
        "assets/site.js?v=20260719prod6",
        "(804) 460-9640",
    ],
    "/robots.txt": ["Sitemap: https://nexgenbinary.com/sitemap.xml"],
    "/sitemap.xml": ["https://nexgenbinary.com/", "2026-07-19"],
    "/privacy/": ["Cookies and Browser Storage"],
}
for route, markers in checks.items():
    request = Request(BASE + route, headers={"User-Agent": "NexGenBinaryProductionCheck/1.0"})
    with urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
        if response.status != 200:
            raise SystemExit(f"{route} returned HTTP {response.status}")
        for marker in markers:
            if marker not in body:
                raise SystemExit(f"{route} is missing: {marker}")
        lowered = body.lower()
        for forbidden in ("googletagmanager", "google-analytics", "assets/analytics.js", "analytics settings"):
            if forbidden in lowered:
                raise SystemExit(f"{route} still contains removed tracking content: {forbidden}")
        print(f"OK {route}")
print("Live production checks passed.")
