#!/usr/bin/env python3
from pathlib import Path
import json
import os
import re
import sys

output = Path(sys.argv[1] if len(sys.argv) > 1 else "assets/analytics-id.js")
measurement_id = os.environ.get("GA4_MEASUREMENT_ID", "").strip().upper()

if measurement_id and not re.fullmatch(r"G-[A-Z0-9]+", measurement_id):
    raise SystemExit("GA4_MEASUREMENT_ID must start with G- and contain only letters and numbers.")

output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(
    "window.NEXGEN_GA4_MEASUREMENT_ID = " + json.dumps(measurement_id) + ";\n",
    encoding="utf-8",
)
print("GA4 analytics enabled." if measurement_id else "GA4 analytics remains disabled: repository variable is empty.")
