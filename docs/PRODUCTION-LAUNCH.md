# Production launch checklist

## GitHub Pages

- Source: GitHub Actions
- Custom domain: `nexgenbinary.com`
- Enforce HTTPS: enabled
- Workflow: `.github/workflows/static.yml`

## DNS

The Microsoft 365 DNS screenshots show the four required GitHub Pages A records
and a `www` CNAME to `jooshondeh.github.io`. Keep the Microsoft 365 MX, SPF,
Autodiscover, DKIM, mobility, SIP, and nameserver records.

Recommended email-security follow-up:

1. Create a mailbox or reporting destination for DMARC aggregate reports.
2. Add `_dmarc` as a TXT record.
3. Start with `p=none`, review legitimate senders, then move gradually to
   `quarantine` and finally `reject`.

## Search and discovery

Submit:

    https://nexgenbinary.com/sitemap.xml

to Google Search Console and Bing Webmaster Tools.

## Integrations

- Formspree: confirm the production domain restriction is `nexgenbinary.com`
- hCaptcha: confirm the allowed hostname includes `nexgenbinary.com`
- Microsoft Bookings: complete a real test booking


## Post-deployment checks

- Submit `https://nexgenbinary.com/sitemap.xml` to Google Search Console and Bing Webmaster Tools.
- Test the homepage with PageSpeed Insights after the deployment cache clears.
- Complete one real contact-form submission and one Microsoft Bookings test.
- Confirm the Google Business Profile website field points to `https://nexgenbinary.com/`.
