#!/usr/bin/env python3
from pathlib import Path
import os
import re
import sys

output = Path(sys.argv[1] if len(sys.argv) > 1 else "assets/analytics-config.js")
requested = os.environ.get("GA4_MEASUREMENT_ID", "").strip().upper()
existing = output.read_text(encoding="utf-8") if output.exists() else ""
existing_match = re.search(r"const measurementId = ['\"](G-[A-Z0-9]+)['\"]", existing, re.I)
existing_id = existing_match.group(1).upper() if existing_match else ""

if requested and not re.fullmatch(r"G-[A-Z0-9]+", requested):
    print("::warning::GA4_MEASUREMENT_ID is invalid. The valid source configuration was preserved when available; deployment will continue.")
    requested = ""

measurement_id = requested or existing_id

content = """(() => {{
  'use strict';

  const measurementId = {measurement!r};
  window.NEXGEN_ANALYTICS_CONFIG = Object.freeze({{
    googleAnalyticsMeasurementId: measurementId,
    requireConsent: true,
    respectDoNotTrack: true
  }});

  if (!/^G-[A-Z0-9]+$/i.test(measurementId)) return;

  const currentScript = document.currentScript;
  const loadAnalytics = () => {{
    if (document.querySelector('script[data-nexgen-analytics-loader]')) return;
    const script = document.createElement('script');
    script.async = true;
    script.dataset.nexgenAnalyticsLoader = '';
    script.src = new URL('analytics.js?v={cache}', currentScript?.src || document.baseURI).href;
    document.head.append(script);
  }};

  if ('requestIdleCallback' in window) {{
    window.requestIdleCallback(loadAnalytics, {{ timeout: 1600 }});
  }} else {{
    window.setTimeout(loadAnalytics, 0);
  }}
}})();
""".format(measurement=measurement_id, cache='20260718prod3')

output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(content, encoding="utf-8")

summary = os.environ.get("GITHUB_STEP_SUMMARY")
message = (
    f"Google Analytics configured with {measurement_id}."
    if measurement_id
    else "Google Analytics is disabled because no GA4 Measurement ID is configured. Deployment continues normally."
)
print(message)
if summary:
    with open(summary, "a", encoding="utf-8") as handle:
        handle.write("## Analytics configuration\\n\\n" + message + "\\n")
