# NexGen Binary public website

Production website repository for **NexGen Binary LLC**.

- Production domain: `https://nexgenbinary.com`
- GitHub repository: `jooshondeh/site-public`
- Deployment: GitHub Pages through `.github/workflows/static.yml`
- Contact form: Formspree + hCaptcha
- Scheduling: Microsoft Bookings
- Google Business: https://share.google/UWWubeCa8CN4sffAM

The deployment workflow publishes only the clean `_site` artifact. Repository
documentation, validation scripts, and workflow files are not exposed as public
website pages.

See `docs/PRODUCTION-LAUNCH.md` before publishing.

## Analytics

Set the GitHub Actions repository variable `GA4_MEASUREMENT_ID` to the real GA4 `G-` ID, then rerun the Pages workflow. See `docs/ANALYTICS-SETUP.md`.

The site intentionally has no web-app manifest, so browsers do not offer an unnecessary “Install NexGen Binary” PWA prompt.
