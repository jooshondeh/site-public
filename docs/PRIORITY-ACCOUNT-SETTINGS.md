# Priority production account settings

These settings live in private third-party dashboards and cannot be changed or
proven by a static ZIP package. The website files are configured to support them.

## 1. Public domain and GitHub Pages

- Repository: `jooshondeh/site-public`
- GitHub Pages source: **GitHub Actions**
- Custom domain: `nexgenbinary.com`
- Enforce HTTPS: enabled after the certificate is issued
- Apex DNS A records: GitHub Pages addresses
- `www` CNAME: `jooshondeh.github.io`

After deployment, run:

```bash
python3 scripts/check_live_site.py
```

The script checks HTTPS, the production title, robots.txt, sitemap.xml, phone
links, analytics assets, Formspree markup, and hCaptcha markup.

## 2. Formspree

In the Formspree project containing `https://formspree.io/f/mdalpbzo`:

- Open **Settings**.
- Set **Restrict to Domain** to `nexgenbinary.com` without `https://` or `www`.
- Submit one real test message from the production Contact form.
- Confirm it reaches the expected inbox and is not placed in Formspree spam.

The website now explicitly uses the `strict-origin-when-cross-origin` referrer
policy, which preserves the origin information required by domain restriction.

## 3. hCaptcha

For site key `267e959c-42c0-45b2-a4d2-45621dbc4f28`:

- Open the hCaptcha dashboard.
- Enable Domain Allowlisting.
- Add the bare hostname `nexgenbinary.com`.
- A bare hostname covers `www.nexgenbinary.com` and other subdomains.
- Save, then complete a real form submission from production.

If the allowlist is disabled or empty, hCaptcha works on any domain; the secure
production setting is to enable it and add `nexgenbinary.com`.
