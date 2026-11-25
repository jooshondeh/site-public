#!/usr/bin/env python3
"""Render an integrated comparison and mobile plan cards from shared content.

Run from any directory: python3 scripts/render_service_plans.py
Use --check to verify committed HTML matches scripts/service-plans.json.
This runs locally; the published site does not require Python or JavaScript to read plans.
"""
from pathlib import Path
from html import escape
import argparse
import json

ROOT = Path(__file__).resolve().parent.parent
START = '<!-- NGB_PLANS_START -->'
END = '<!-- NGB_PLANS_END -->'

BOOKING_URL = 'https://outlook.office.com/book/MeetNexGenBinary@nexgenbinary.com/'

def plan_intro(plan, heading_id):
    return (
        f'<span class="plan-summary-badge">{escape(plan["badge"])}</span>'
        f'<h3 id="{escape(heading_id)}"><span class="plan-family">Managed IT</span> '
        f'<span class="plan-name">{escape(plan["short"])}</span></h3>'
        '<p class="plan-summary-price">Custom monthly quote</p>'
        f'<p class="plan-summary-description">{escape(plan["description"])}</p>'
    )

def quote_link(plan):
    title = escape(plan['name'])
    style = 'button-primary' if plan['recommended'] else 'button-outline'
    return (
        f'<a class="button {style}" href="{BOOKING_URL}" data-booking-open="" '
        f'data-booking-plan="{title}" aria-label="Request a quote for {title}" '
        'aria-haspopup="dialog" aria-controls="nb-booking-modal" '
        'target="_blank" rel="noopener">Request a Quote</a>'
    )

def render(data):
    plans, rows = data['plans'], data['features']
    parts = ['<div class="plan-comparison-content" id="plan-comparison">']
    parts.append('<div class="plan-comparison-wrap"><table id="plan-comparison-table" class="plan-comparison">')
    parts.append('<caption class="sr-only">Managed IT service plan comparison</caption><colgroup><col class="feature-column"/><col/><col class="recommended-column"/><col/></colgroup>')
    parts.append('<thead><tr><th scope="col" id="coverage-feature" class="comparison-corner"><span>Service features</span></th>')
    for plan in plans:
        key = escape(plan['key'])
        featured = ' is-recommended' if plan['recommended'] else ''
        parts.append(f'<th scope="col" id="plan-{key}" class="plan-column-head{featured}" data-plan-header="{key}" aria-labelledby="plan-{key}-title">')
        parts.append(plan_intro(plan, f'plan-{key}-title'))
        parts.append('</th>')
    parts.append('</tr></thead><tbody>')
    for row in rows:
        key = escape(row['key'])
        parts.append(f'<tr data-feature="{key}"><th scope="row" id="feature-{key}">{escape(row["name"])}</th>')
        for i, plan in enumerate(plans):
            parts.append(f'<td headers="feature-{key} plan-{escape(plan["key"])}">{escape(row["values"][i])}</td>')
        parts.append('</tr>')
    parts.append('</tbody><tfoot><tr><th scope="row"><span class="sr-only">Request a quote</span></th>')
    for plan in plans:
        parts.append(f'<td>{quote_link(plan)}</td>')
    parts.append('</tr></tfoot></table></div>')
    parts.append('<div class="plan-summaries plan-mobile-summaries">')
    for i, plan in enumerate(plans):
        key = escape(plan['key'])
        featured = ' is-recommended' if plan['recommended'] else ''
        attrs = ' data-recommended="true"' if plan['recommended'] else ''
        parts.append(f'<article class="plan-summary{featured}" data-plan="{key}"{attrs}>')
        parts.append(plan_intro(plan, f'mobile-plan-{key}-title'))
        parts.append(f'<details class="plan-mobile-details"><summary>Explore {escape(plan["short"])} features</summary><dl>')
        for row in rows:
            parts.append(f'<div data-feature="{escape(row["key"])}"><dt>{escape(row["name"])}</dt><dd>{escape(row["values"][i])}</dd></div>')
        parts.append('</dl></details>')
        parts.append(quote_link(plan))
        parts.append('</article>')
    parts.append('</div></div>')
    return '\n'.join(parts)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    data=json.loads((ROOT/'scripts/service-plans.json').read_text())
    html=(ROOT/'index.html').read_text()
    if html.count(START)!=1 or html.count(END)!=1:
        raise SystemExit('The homepage must contain one pair of NGB_PLANS markers.')
    before,rest=html.split(START)
    old,after=rest.split(END)
    generated='\n'+render(data)+'\n'
    if args.check:
        if old!=generated:
            raise SystemExit('Plan markup differs from its source. Run python3 scripts/render_service_plans.py and commit index.html together with service-plans.json.')
        print('Unified desktop comparison and mobile plan cards match the shared content source.')
    else:
        (ROOT/'index.html').write_text(before+START+generated+END+after)
        print('Rendered three service plans from scripts/service-plans.json.')

if __name__=='__main__':
    main()
