# Analytics setup

The production package includes privacy-conscious Google Analytics 4 support,
but tracking is **disabled by default** because no Measurement ID was provided.

## Enable traffic reporting

1. Create a Google Analytics account and one GA4 property for NexGen Binary.
2. Create a Web data stream for `https://nexgenbinary.com/`.
3. Copy the Measurement ID beginning with `G-`.
4. Open `assets/analytics-config.js`.
5. Enter the ID:

```js
googleAnalyticsMeasurementId: "G-YOURREALID"
```

6. Commit the change and verify traffic in the GA4 Realtime report.

When enabled, the site can report:

- page views and referral sources
- browser/device categories and approximate regions
- phone, email, booking, and Google Business clicks
- contact-form starts and successful submissions
- scroll depth
- LCP, CLS, and INP performance metrics

The analytics code does not send form field values, names, email addresses,
phone numbers, practice names, message content, or hCaptcha responses.

`requireConsent` defaults to `true`, so a consent banner appears only after a
valid Measurement ID is entered. The banner does not appear while analytics is
disabled.
