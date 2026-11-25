# NexGen Binary public website

Production static website for **NexGen Binary LLC**.

- Website: https://nexgenbinary.com/
- Repository: `jooshondeh/site-public`
- Hosting: GitHub Pages through `.github/workflows/static.yml`
- Current release: `production-2026-11-25-v9-blue-brand`
- Shared asset cache version: `20261125brand9`
- Contact form: Formspree with deferred hCaptcha verification
- Scheduling: Microsoft Bookings, with a visible separate-tab fallback

## Release documentation

See [v9 release notes](docs/RELEASE-NOTES-v9.md) for branding, responsive fixes,
testing scope, upload instructions and production verification limits.
The machine-readable results are in [the compatibility audit](docs/COMPATIBILITY-AUDIT.json).

## Validation

```bash
python3 scripts/validate_site.py .
node --check assets/site.js
```

After deployment, an optional public read-only check is available:

```bash
python3 scripts/check_live_site.py
```

The existing workflow builds from an explicit file allowlist, validates source
and clean output, and excludes repository documentation/scripts from the public
deployment. Keep that workflow and the shared validator synchronized with release
metadata. The public hCaptcha site key and Formspree endpoint are client-side
configuration; provider delivery and booking access require a live post-deploy check.
