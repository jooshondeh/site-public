#!/usr/bin/env python3
from html.parser import HTMLParser
from urllib.request import Request, urlopen
import sys

ORIGIN = "https://nexgenbinary.com"

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.manifest = False
        self.phone_links = 0
        self.formspree = False
        self.hcaptcha = False
        self.analytics_id = False
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "title": self.in_title = True
        if tag == "link" and "manifest" in data.get("rel", "").split(): self.manifest = True
        if tag == "a" and data.get("href") == "tel:+18044609640": self.phone_links += 1
        if data.get("action") == "https://formspree.io/f/mdalpbzo": self.formspree = True
        if data.get("data-sitekey") == "267e959c-42c0-45b2-a4d2-45621dbc4f28": self.hcaptcha = True
        if "analytics-id.js" in data.get("src", ""): self.analytics_id = True
    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False
    def handle_data(self, data):
        if self.in_title: self.title += data

def fetch(path):
    request = Request(ORIGIN + path, headers={"User-Agent": "NexGenBinaryLaunchCheck/1.0"})
    with urlopen(request, timeout=20) as response:
        return response.status, response.geturl(), response.read().decode("utf-8", "replace")

errors = []
try:
    status, final_url, home = fetch("/")
    parser = PageParser(); parser.feed(home)
    if status != 200: errors.append(f"Homepage returned {status}")
    if final_url != ORIGIN + "/": errors.append(f"Homepage redirected to {final_url}")
    if parser.title.strip() != "NexGen Binary": errors.append(f"Unexpected title: {parser.title!r}")
    if parser.manifest: errors.append("Installable web-app manifest is still linked")
    if parser.phone_links != 4: errors.append(f"Expected 4 homepage phone links, found {parser.phone_links}")
    if not parser.formspree: errors.append("Formspree form action is missing")
    if not parser.hcaptcha: errors.append("hCaptcha site key is missing")
    if not parser.analytics_id: errors.append("Analytics ID loader is missing")

    _, _, robots = fetch("/robots.txt")
    if "Disallow: /" in robots or "Sitemap: https://nexgenbinary.com/sitemap.xml" not in robots:
        errors.append("robots.txt is not production-ready")

    _, _, sitemap = fetch("/sitemap.xml")
    if "https://nexgenbinary.com/" not in sitemap:
        errors.append("sitemap.xml is missing the production URL")
except Exception as exc:
    errors.append(f"Live-site request failed: {exc}")

if errors:
    print("LIVE CHECK FAILED")
    for error in errors: print("-", error)
    sys.exit(1)

print("LIVE CHECK PASSED")
print("Note: Formspree Restrict to Domain and hCaptcha Domain Allowlisting are private dashboard settings and still require one real production form submission to verify.")
