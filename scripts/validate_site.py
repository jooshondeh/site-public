#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote, parse_qs
import argparse
import json
import re
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description="Validate the NexGen Binary production website.")
parser.add_argument("root", nargs="?", default=".")
parser.add_argument("--clean", action="store_true")
args = parser.parse_args()

ROOT = Path(args.root).resolve()
PRODUCTION_ORIGIN = "https://nexgenbinary.com"
BUILD = "production-2026-11-25-v12-brand-booking"
CACHE = "20261125brand12"
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
REPOSITORY_ONLY_REQUIRED = ["scripts/service-plans.json", "scripts/render_service_plans.py"]
REQUIRED = SOURCE_REQUIRED + (DEPLOYMENT_ONLY_REQUIRED if args.clean else REPOSITORY_ONLY_REQUIRED)
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
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

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
        # A small element tree supports structural checks without an HTML dependency.
        self.elements = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        element = {"tag": tag, "attrs": data, "parent": self.stack[-1] if self.stack else None, "text": []}
        self.elements.append(element)
        if tag not in self.VOID_TAGS:
            self.stack.append(element)
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
        for position in range(len(self.stack) - 1, -1, -1):
            if self.stack[position]["tag"] == tag:
                del self.stack[position:]
                break

    def handle_data(self, data):
        if self.in_phone_display and self.phone_display_texts:
            self.phone_display_texts[-1] += data
        if self.in_json_ld:
            self.json_ld[-1] += data
        if not any(element["tag"] in ("script", "style", "svg") for element in self.stack):
            for element in self.stack:
                element["text"].append(data)


def element_text(element):
    """Normalize readable text without depending on line breaks or nested spans."""
    return " ".join(" ".join(element["text"]).split())


def inside(element, ancestor):
    parent = element["parent"]
    while parent is not None:
        if parent is ancestor:
            return True
        parent = parent["parent"]
    return False


def validate_header_slogan(parsed):
    headers = [e for e in parsed.elements if e["tag"] == "header" and "site-header" in e["attrs"].get("class", "").split()]
    brands = [e for e in parsed.elements if e["tag"] == "a" and "brand" in e["attrs"].get("class", "").split() and any(inside(e, header) for header in headers)]
    slogans = [e for e in parsed.elements if "brand-tagline" in e["attrs"].get("class", "").split() and any(inside(e, brand) for brand in brands)]
    if len(headers) != 1 or len(brands) != 1 or len(slogans) != 1 or element_text(slogans[0]) != "Virginia's Trusted IT Partner":
        return ["header brand link must contain one brand-tagline reading Virginia's Trusted IT Partner"]
    return []


def public_copy_issues(parsed):
    """Inspect readable page copy, not JavaScript, SVG paths, CSS, or metadata."""
    body = next((element for element in parsed.elements if element["tag"] == "body"), None)
    if body is None:
        return ["missing body element"]
    copy = element_text(body)
    issues = []
    if re.search(r"[$£€]\s*\d|\b(?:USD|GBP|EUR)\s*\d|\b\d[\d,.]*\s*(?:USD|GBP|EUR)\b", copy, re.IGNORECASE):
        issues.append("numeric public pricing found; this release uses custom quotes")
    if re.search(r"\b\d[\d,.]*\s*(?:/|per\s+)(?:month|mo\b|workstation|server|user)\b", copy, re.IGNORECASE):
        issues.append("numeric recurring rates found in public copy")
    obsolete = {
        "Managed IT Complete": r"\bManaged\s+IT\s+Complete\b",
        "three-year hardware warranty": r"\b(?:three|3)[\s-]+year\b[^.]{0,40}\bwarrant(?:y|ies)\b",
        "included server loaners": r"\b(?:server loaners?|loaner servers?)\b[^.]{0,60}\bincluded\b|\bloaner equipment\b[^.]{0,40}\bincluded\b[^.]{0,30}\bservers\b",
        "internal rate guidance": r"\binternal\s+(?:monthly\s+minimums?|workstation\s+rates?|server\s+rates?)\b",
    }
    for label, pattern in obsolete.items():
        if re.search(pattern, copy, re.IGNORECASE):
            issues.append(f"obsolete or internal offer text found: {label}")
    return issues


def validate_plan_structure(parsed):
    """Check the usable comparison, mobile parity, quote links, and form choice."""
    issues = []
    names = {
        "essentials": "Managed IT Essentials",
        "standard": "Managed IT Standard",
        "premium": "Managed IT Premium",
    }
    features = [
        "remote-support", "maintenance", "endpoint-protection", "monitoring-alerts",
        "backup-management", "restore-testing", "backup-reporting", "vendor-coordination",
        "onsite-maintenance", "technology-planning", "warranty-coordination", "loaner-equipment", "after-hours",
    ]
    booking_url = "https://outlook.office.com/book/MeetNexGenBinary@nexgenbinary.com/"

    def valid_quote_link(element, name):
        attrs = element["attrs"]
        return (
            element["tag"] == "a" and attrs.get("data-booking-plan") == name
            and "data-booking-open" in attrs and attrs.get("href") == booking_url
            and attrs.get("target") == "_blank" and "noopener" in attrs.get("rel", "").split()
            and attrs.get("aria-haspopup") == "dialog" and attrs.get("aria-controls") == "nb-booking-modal"
        )

    if any("data-plan-select" in e["attrs"] for e in parsed.elements):
        issues.append("obsolete data-plan-select quote routing must be removed")
    cards = [e for e in parsed.elements if e["tag"] == "article" and "plan-summary" in e["attrs"].get("class", "").split()]
    if len(cards) != 3 or sorted(e["attrs"].get("data-plan", "") for e in cards) != sorted(names):
        issues.append("expected exactly three plan summaries: essentials, standard, premium")
    recommended = [e for e in cards if e["attrs"].get("data-recommended") == "true"]
    if len(recommended) != 1 or recommended[0]["attrs"].get("data-plan") != "standard":
        issues.append("Standard must be the only recommended plan")
    mobile_containers = [e for e in parsed.elements if {"plan-summaries", "plan-mobile-summaries"}.issubset(e["attrs"].get("class", "").split())]
    if len(mobile_containers) != 1 or any(not inside(card, mobile_containers[0]) for card in cards):
        issues.append("all three mobile plans must be inside one plan-summaries.plan-mobile-summaries container")
    for card in cards:
        key = card["attrs"].get("data-plan")
        expected_name = names.get(key)
        headings = [element_text(e) for e in parsed.elements if e["tag"] in ("h2", "h3", "h4") and inside(e, card)]
        if expected_name not in headings:
            issues.append(f"plan {key!r} is missing its full heading")
        if element_text(card).count("Custom monthly quote") != 1:
            issues.append(f"plan {key!r} must show Custom monthly quote once")
        links = [e for e in parsed.elements if "data-booking-plan" in e["attrs"] and inside(e, card)]
        if len(links) != 1 or not valid_quote_link(links[0], expected_name):
            issues.append(f"plan {key!r} requires one accessible booking quote link with a native calendar fallback")

    links = [e for e in parsed.elements if "data-booking-plan" in e["attrs"]]
    if len(links) != 6:
        issues.append("expected six plan quote links across summaries and table footer")
    for name in names.values():
        matches = [e for e in links if e["attrs"].get("data-booking-plan") == name]
        if len(matches) != 2 or any(not valid_quote_link(e, name) for e in matches):
            issues.append(f"{name} requires one desktop and one mobile booking quote link")

    containers = [e for e in parsed.elements if e["attrs"].get("id") == "plan-comparison"]
    if len(containers) != 1 or containers[0]["tag"] != "div" or "plan-comparison-content" not in containers[0]["attrs"].get("class", "").split():
        issues.append("plan-comparison must be a shared div.plan-comparison-content anchor for all screen sizes")
    elif any(not inside(card, containers[0]) for card in cards):
        issues.append("the shared comparison anchor must contain all three plan summaries")
    tables = [e for e in parsed.elements if e["attrs"].get("id") == "plan-comparison-table"]
    table_values = {}
    if len(tables) != 1 or tables[0]["tag"] != "table" or "plan-comparison" not in tables[0]["attrs"].get("class", "").split():
        issues.append("expected one semantic table with id plan-comparison-table and class plan-comparison")
    else:
        table = tables[0]
        if len(containers) == 1 and not inside(table, containers[0]):
            issues.append("the comparison table must be inside the shared plan-comparison anchor")
        captions = [e for e in parsed.elements if e["tag"] == "caption" and inside(e, table)]
        if len(captions) != 1 or not element_text(captions[0]) or "sr-only" not in captions[0]["attrs"].get("class", "").split():
            issues.append("plan comparison requires one readable, visually hidden sr-only caption")
        heads = [e for e in parsed.elements if e["tag"] == "thead" and inside(e, table)]
        header_rows = [e for e in parsed.elements if e["tag"] == "tr" and any(inside(e, head) for head in heads)]
        columns = [e for e in parsed.elements if e["tag"] in ("th", "td") and any(e["parent"] is row for row in header_rows)]
        if len(heads) != 1 or len(header_rows) != 1 or len(columns) != 4 or any(e["tag"] != "th" or e["attrs"].get("scope") != "col" for e in columns):
            issues.append("plan comparison header must have one feature column and three plan columns using th scope=col")
        column_ids = [e["attrs"].get("id") for e in columns]
        if len(column_ids) != 4 or any(not value for value in column_ids) or len(set(column_ids)) != 4:
            issues.append("all four comparison column headers require unique IDs")
        plan_headers = [e for e in columns if "data-plan-header" in e["attrs"]]
        if len(plan_headers) != 3 or [e["attrs"].get("data-plan-header") for e in plan_headers] != list(names):
            issues.append("the unified table requires the three plan introductions in its column headers")
        for header in plan_headers:
            key = header["attrs"].get("data-plan-header")
            title_id = f"plan-{key}-title"
            titles = [e for e in parsed.elements if e["tag"] == "h3" and e["attrs"].get("id") == title_id and inside(e, header)]
            if header["attrs"].get("id") != f"plan-{key}" or header["attrs"].get("aria-labelledby", "").split() != [title_id] or len(titles) != 1 or element_text(titles[0]) != names.get(key):
                issues.append(f"desktop plan {key!r} requires a full h3 heading and matching accessible column name")
            if element_text(header).count("Custom monthly quote") != 1:
                issues.append(f"desktop plan {key!r} must show Custom monthly quote once")
            if any(("data-booking-plan" in e["attrs"] or "data-booking-open" in e["attrs"]) and inside(e, header) for e in parsed.elements):
                issues.append(f"desktop plan {key!r} must not repeat its footer booking action in the header")
            if ("Recommended" in element_text(header)) != (key == "standard"):
                issues.append("Standard must be the only recommended desktop plan")
        bodies = [e for e in parsed.elements if e["tag"] == "tbody" and inside(e, table)]
        rows = [e for e in parsed.elements if e["tag"] == "tr" and any(inside(e, body) for body in bodies)]
        row_keys = [row["attrs"].get("data-feature", "") for row in rows]
        if len(rows) != 13 or sorted(row_keys) != sorted(features):
            issues.append("comparison body must contain the 13 distinct agreed service features")
        for row in rows:
            key = row["attrs"].get("data-feature", "unknown")
            cells = [e for e in parsed.elements if e["parent"] is row and e["tag"] in ("th", "td")]
            if len(cells) != 4 or cells[0]["tag"] != "th" or cells[0]["attrs"].get("scope") != "row" or any(e["tag"] != "td" for e in cells[1:]):
                issues.append(f"comparison feature {key}: expected a row header and three data cells")
                continue
            row_id = cells[0]["attrs"].get("id")
            if not row_id or not element_text(cells[0]):
                issues.append(f"comparison feature {key}: row header needs an ID and readable label")
            for position, cell in enumerate(cells[1:], start=1):
                refs = set(cell["attrs"].get("headers", "").split())
                if len(column_ids) == 4 and (not {row_id, column_ids[position]}.issubset(refs) or not refs.issubset(parsed.ids)):
                    issues.append(f"comparison feature {key}: data cell {position} must reference its row and column headers")
                if not element_text(cell):
                    issues.append(f"comparison feature {key}: data cell {position} is empty")
            table_values[key] = [element_text(cell) for cell in cells]
        feet = [e for e in parsed.elements if e["tag"] == "tfoot" and inside(e, table)]
        footer_links = [e for e in links if any(inside(e, foot) for foot in feet)]
        if len(feet) != 1 or len(footer_links) != 3:
            issues.append("comparison footer requires one quote link for each plan")

    for card in cards:
        key = card["attrs"].get("data-plan")
        mobile = [e for e in parsed.elements if e["tag"] == "details" and "plan-mobile-details" in e["attrs"].get("class", "").split() and inside(e, card)]
        if len(mobile) != 1:
            issues.append(f"plan {key!r} requires one native mobile details disclosure")
            continue
        summaries = [e for e in parsed.elements if e["tag"] == "summary" and e["parent"] is mobile[0]]
        if len(summaries) != 1 or not element_text(summaries[0]):
            issues.append(f"plan {key!r} mobile disclosure requires a readable summary")
        card_links = [e for e in links if inside(e, card)]
        element_order = {id(e): position for position, e in enumerate(parsed.elements)}
        last_detail_position = max(element_order[id(e)] for e in parsed.elements if e is mobile[0] or inside(e, mobile[0]))
        if len(card_links) == 1 and element_order[id(card_links[0])] <= last_detail_position:
            issues.append(f"plan {key!r} mobile booking action must follow its feature disclosure")
        lists = [e for e in parsed.elements if e["tag"] == "dl" and inside(e, mobile[0])]
        mobile_rows = [e for e in parsed.elements if e["tag"] == "div" and "data-feature" in e["attrs"] and any(inside(e, listing) for listing in lists)]
        if len(lists) != 1 or len(mobile_rows) != 13 or sorted(e["attrs"].get("data-feature", "") for e in mobile_rows) != sorted(features):
            issues.append(f"plan {key!r} mobile details must contain all 13 agreed features")
        column = list(names).index(key) + 1 if key in names else None
        for row in mobile_rows:
            feature = row["attrs"].get("data-feature")
            terms = [e for e in parsed.elements if e["tag"] == "dt" and e["parent"] is row]
            definitions = [e for e in parsed.elements if e["tag"] == "dd" and e["parent"] is row]
            if len(terms) != 1 or len(definitions) != 1:
                issues.append(f"plan {key!r}, mobile feature {feature}: expected one dt and one dd")
                continue
            values = table_values.get(feature)
            if values and column is not None and (element_text(terms[0]) != values[0] or element_text(definitions[0]) != values[column]):
                issues.append(f"plan {key!r}, mobile feature {feature}: label/value differs from desktop comparison")

    interests = [e for e in parsed.elements if e["attrs"].get("id") == "contact-interest"]
    if len(interests) != 1 or interests[0]["tag"] != "select" or interests[0]["attrs"].get("name") != "interest":
        issues.append("contact form requires native select id=contact-interest name=interest")
    else:
        interest = interests[0]
        options = [e["attrs"].get("value", element_text(e)) for e in parsed.elements if e["tag"] == "option" and inside(e, interest)]
        expected_options = set(names.values()) | {"Help me choose", "Project or one-time support"}
        if set(options) - {""} != expected_options or len(options) != len(set(options)):
            issues.append("contact interest choices must match the three plan names, Help me choose, and Project or one-time support")
        if not any(e["tag"] == "label" and e["attrs"].get("for") == "contact-interest" and element_text(e) for e in parsed.elements):
            issues.append("contact interest select requires a visible associated label")
        if not any(e["tag"] == "form" and inside(interest, e) and e["attrs"].get("action") == "https://formspree.io/f/mdalpbzo" for e in parsed.elements):
            issues.append("contact interest must be inside the existing Formspree contact form")

    for section_id in ("additional-services", "coverage-questions"):
        sections = [e for e in parsed.elements if e["tag"] == "section" and e["attrs"].get("id") == section_id]
        if len(sections) != 1:
            issues.append(f"expected one section #{section_id}")
        elif section_id == "coverage-questions":
            disclosures = [e for e in parsed.elements if e["tag"] == "details" and inside(e, sections[0])]
            if not disclosures:
                issues.append("coverage questions must use native details disclosures")
            for detail in disclosures:
                summaries = [e for e in parsed.elements if e["tag"] == "summary" and e["parent"] is detail]
                if len(summaries) != 1 or not element_text(summaries[0]):
                    issues.append("each coverage question requires a readable summary")
    return issues


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
    for issue in validate_header_slogan(parsed):
        errors.append(f"{relative}: {issue}")
    for issue in public_copy_issues(parsed):
        errors.append(f"{relative}: {issue}")
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
for issue in validate_plan_structure(documents[ROOT / "index.html"]):
    errors.append(f"index.html: {issue}")

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

if not args.clean:
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/render_service_plans.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        )
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()
            errors.append(f"Service-plan source/render parity check failed: {detail or 'renderer returned a failure'}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"Could not verify canonical service-plan content: {exc}")

if errors:
    raise SystemExit("\n".join(errors))

print(
    f"Validated {len(html_files)} HTML files, {phone_count} native phone links, "
    f"{logo_count} updated logos, {anchor_count} local anchors, {aria_count} ARIA references, "
    "unified plan comparison and mobile parity, booking quote actions, header slogans, asset versions, CSS custom properties, blue branding, business hours, social links, "
    "no tracking code, SEO metadata, and integration hooks. "
    "Static checks do not verify external form delivery or bookings."
)
