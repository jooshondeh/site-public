# Production deployment checklist

## GitHub Pages

1. In **Settings → Pages**, choose **GitHub Actions** as the source.
2. Set the custom domain to `nexgenbinary.com`.
3. Enable **Enforce HTTPS** when available.
4. The workflow must include `include-hidden-files: true` in the Pages upload
   step. This package includes that correction.

The workflow generates `CNAME`, `.nojekyll`, and
`.well-known/security.txt` inside `_site`; do not upload those source files.

## Analytics

Analytics is optional and never blocks deployment. Follow
`docs/ANALYTICS-SETUP.md` to create a GA4 web stream and add the repository
variable.

## External account checks

- Formspree **Restrict to Domain**: `nexgenbinary.com`
- hCaptcha allowlisted hostname: `nexgenbinary.com`
- Google Search Console: verify the domain and submit
  `https://nexgenbinary.com/sitemap.xml`

## Post-deployment checks

- Home, Privacy, Terms, Booking, and 404 pages
- mobile navigation at phone and tablet widths
- all phone links and email links
- hCaptcha loading near the contact section
- successful Formspree delivery
- Microsoft Bookings modal and direct booking page
- Google Business link
- Realtime Analytics after consent, when configured
