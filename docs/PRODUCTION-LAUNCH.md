# Production launch checklist

This package is configured for:

- Repository: `jooshondeh/site-public`
- Primary production URL: `https://nexgenbinary.com/`
- Google Business Profile: `https://share.google/UWWubeCa8CN4sffAM`

## 1. Replace the repository cleanly

Delete the old contents of `site-public`, then upload the contents of this
package at the repository root. Do not upload the outer ZIP or place everything
inside another folder.

The hidden `.github` directory contains the deployment workflow. GitHub Desktop
or Git is the most reliable way to preserve it. When using the GitHub website,
create `.github/workflows/static.yml` through **Add file → Create new file** if
the hidden directory is not uploaded.

## 2. Configure GitHub Pages

In **Settings → Pages**:

1. Set **Source** to **GitHub Actions**.
2. Enter the custom domain: `nexgenbinary.com`.
3. Save and enable **Enforce HTTPS** when it becomes available.

The repository contains a `CNAME` file for documentation and branch-deployment
compatibility, but a custom Actions workflow still requires the domain to be
set in GitHub Pages settings.

## 3. Configure DNS

For the apex domain, add GitHub Pages A records:

- `185.199.108.153`
- `185.199.109.153`
- `185.199.110.153`
- `185.199.111.153`

Add a `www` CNAME pointing to:

- `jooshondeh.github.io`

Configure `nexgenbinary.com` as the primary domain in GitHub Pages so `www`
redirects to the apex domain. Verify the domain in GitHub account Pages settings
before launch when possible, and do not use wildcard DNS records.

## 4. Confirm production behavior

Verify:

- Home, Privacy, Terms, Booking, and 404 pages
- mobile navigation at phone and tablet widths
- all phone links open the call application
- the unwanted green phone badge remains absent
- email links open the mail application
- consultation buttons open Microsoft Bookings
- Formspree messages arrive successfully after hCaptcha
- the Google G icon opens the direct Business Profile
- HTTPS is enforced

## 5. Search engine launch

1. Add a **Domain property** for `nexgenbinary.com` in Google Search Console.
2. Verify ownership with the DNS TXT record provided by Search Console.
3. Submit: `https://nexgenbinary.com/sitemap.xml`
4. Inspect `https://nexgenbinary.com/` and request indexing.
5. Add the same site to Bing Webmaster Tools; importing from Search Console is
   usually the quickest path.
6. Update the Google Business Profile website field to:
   `https://nexgenbinary.com/`

The production package already includes:

- crawlable robots.txt
- XML sitemap
- canonical URLs
- Open Graph and large social-sharing image
- Organization, WebSite, and ProfessionalService structured data
- indexable Home, Privacy, and Terms pages
- noindex utility Booking and 404 pages
- direct Google Business relationship markup
- descriptive meta descriptions
- a security contact file

## 6. Analytics

Follow `docs/ANALYTICS-SETUP.md`. No analytics data is collected until a real
GA4 Measurement ID is entered.

## 7. Recommended content growth after launch

Do not create thin or repetitive location pages. The strongest future SEO work
would be useful, original pages such as:

- Managed IT for dental practices
- Dental cybersecurity and backup planning
- Microsoft 365 for dental offices
- Dental network and Wi-Fi upgrades
- VoIP, business audio, and camera solutions
- Dental IT support in Richmond and Northern Virginia
- anonymized case studies and practical technology guides

Each future page should answer real buyer questions, contain unique content,
and link naturally to consultation and contact options.
