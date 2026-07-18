# NexGen Binary public website

Production repository for **NexGen Binary LLC**.

- Website: `https://nexgenbinary.com`
- Repository: `jooshondeh/site-public`
- Deployment: `.github/workflows/static.yml`
- Contact form: Formspree + hCaptcha
- Scheduling: Microsoft Bookings
- Analytics: optional GA4; deployment succeeds whether configured or not

The workflow publishes only the allowlisted `_site` artifact. Hidden production
files are generated during deployment, so `.nojekyll`, `.well-known`, and
`CNAME` do not need to be uploaded through GitHub's browser interface.
