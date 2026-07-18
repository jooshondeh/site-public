# Google Analytics setup and access

The website is ready for Google Analytics 4, but a real GA4 Measurement ID is
required. A Measurement ID begins with `G-` and is created in Google Analytics,
not in GitHub.

## Create the GA4 property and web stream

1. Sign in to Google Analytics.
2. Create or select the NexGen Binary property.
3. Open **Admin → Data streams → Add stream → Web**.
4. Use `https://nexgenbinary.com/` as the website URL.
5. Copy the Measurement ID beginning with `G-`.

## Add it in the GitHub screen shown in the screenshot

1. Open `site-public → Settings → Secrets and variables → Actions`.
2. Select the **Variables** tab.
3. Under **Repository variables**, select **New repository variable**.
4. Enter:

```
Name: GA4_MEASUREMENT_ID
Value: G-YOUR-REAL-ID
```

5. Commit any change or run the Pages workflow manually.
6. Open the workflow's **Configure optional Google Analytics** step. It will
   state whether analytics was enabled or left disabled.

No variable is required for deployment. Missing or invalid analytics settings
produce a warning and disable analytics rather than failing the website build.

## Alternative without a GitHub variable

A real Measurement ID may be entered in `assets/analytics-config.js` as the
`measurementId`. The workflow preserves a valid source ID when no repository
variable exists. The repository variable is preferred because it is easier to
change without editing website code.

## Verify and access the data

After granting analytics consent on the website, use:

- **Reports → Realtime** to confirm current visits and events.
- **Reports → Acquisition** for search, direct, referral, and campaign traffic.
- **Reports → Engagement → Pages and screens** for content usage.
- **Reports → Engagement → Events** for phone, email, booking, and form events.
- **Explore** for custom funnels and comparisons.

Tracked business events include:

- `click_to_call`
- `email_click`
- `booking_click`
- `google_business_click`
- `contact_form_start`
- `generate_lead`
- `contact_form_error`
- `section_view`
- `scroll_depth`
- `web_vital`

The analytics code does not send form names, email addresses, phone entries,
practice names, messages, or hCaptcha responses.
