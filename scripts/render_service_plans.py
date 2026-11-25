#!/usr/bin/env python3
"""Render desktop comparison and mobile plan details from one shared content file.

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

def render(data):
    plans = data['plans']
    rows = data['features']
    parts = ['<div class="plan-comparison-content" id="plan-comparison"><div class="plan-summaries">']
    for i, plan in enumerate(plans):
        featured = ' is-recommended' if plan['recommended'] else ''
        attrs = ' data-recommended="true"' if plan['recommended'] else ''
        title = escape(plan['name'])
        parts.append(f'<article class="plan-summary{featured}" data-plan="{escape(plan["key"])}"{attrs}>')
        parts.append(f'<span class="plan-summary-badge">{escape(plan["badge"])}</span>')
        parts.append(f'<h3>{title}</h3><p class="plan-summary-price">Custom monthly quote</p>')
        parts.append(f'<p class="plan-summary-description">{escape(plan["description"])}</p>')
        style = 'button-primary' if plan['recommended'] else 'button-outline'
        parts.append(f'<a class="button {style}" href="#contact-form" data-plan-select="{title}" aria-label="Request a quote for {title}">Request a Quote</a>')
        parts.append(f'<details class="plan-mobile-details"><summary>Explore {escape(plan["short"])} features</summary><dl>')
        for row in rows:
            parts.append(f'<div data-feature="{escape(row["key"])}"><dt>{escape(row["name"])}</dt><dd>{escape(row["values"][i])}</dd></div>')
        parts.append('</dl></details></article>')
    parts.append('</div>')
    parts.append('<div class="plan-comparison-wrap"><table id="plan-comparison-table" class="plan-comparison">')
    parts.append('<caption>Compare managed IT coverage</caption><colgroup><col class="feature-column"/><col/><col class="recommended-column"/><col/></colgroup>')
    parts.append('<thead><tr><th scope="col" id="coverage-feature">Service feature</th>')
    for plan in plans:
        parts.append(f'<th scope="col" id="plan-{escape(plan["key"])}">{escape(plan["short"])}'+(' <span class="table-recommendation">Recommended</span>' if plan['recommended'] else '')+'</th>')
    parts.append('</tr></thead><tbody>')
    for row in rows:
        key=escape(row['key'])
        parts.append(f'<tr data-feature="{key}"><th scope="row" id="feature-{key}">{escape(row["name"])}</th>')
        for i,plan in enumerate(plans):
            parts.append(f'<td headers="feature-{key} plan-{escape(plan["key"])}">{escape(row["values"][i])}</td>')
        parts.append('</tr>')
    parts.append('</tbody><tfoot><tr><th scope="row">Find your fit</th>')
    for plan in plans:
        title=escape(plan['name'])
        style='button-primary' if plan['recommended'] else 'button-outline'
        parts.append(f'<td><a class="button {style} button-small" href="#contact-form" data-plan-select="{title}" aria-label="Request a quote for {title}">Request a Quote</a></td>')
    parts.append('</tr></tfoot></table></div></div>')
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
        print('Plan summaries, desktop table, and mobile details match the shared content source.')
    else:
        (ROOT/'index.html').write_text(before+START+generated+END+after)
        print('Rendered three service plans from scripts/service-plans.json.')

if __name__=='__main__':
    main()
