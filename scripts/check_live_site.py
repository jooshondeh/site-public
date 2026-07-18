#!/usr/bin/env python3
from urllib.request import Request, urlopen

BASE = "https://nexgenbinary.com"
MEASUREMENT_ID = "G-YY6Q8RTE7R"

checks = {
    "/": [
        "Dental IT Support &amp; Managed Services in Virginia | NexGen Binary",
        f"gtag/js?id={MEASUREMENT_ID}",
        "data-nexgen-google-tag",
        "assets/analytics.js?v=20260718prod5",
        "(804) 460-9640",
    ],
    "/robots.txt": ["Sitemap: https://nexgenbinary.com/sitemap.xml"],
    "/sitemap.xml": ["https://nexgenbinary.com/"],
    "/privacy/": ["Google Analytics is configured with Consent Mode"],
}

for route, markers in checks.items():
    request = Request(
        BASE + route,
        headers={"User-Agent": "NexGenBinaryProductionCheck/1.0"},
    )
    with urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
        if response.status != 200:
            raise SystemExit(f"{route} returned HTTP {response.status}")
        for marker in markers:
            if marker not in body:
                raise SystemExit(f"{route} is missing: {marker}")
        print(f"OK {route}")

print("Live production checks passed.")
