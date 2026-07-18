# Google Analytics 4 activation and access

The website code and deployment workflow are fully configured for GA4. A real
Measurement ID is still required because Google assigns it inside the business
owner's Analytics account; it cannot be generated from website files.

## Activate analytics without editing website files

1. Sign in at Google Analytics and create one GA4 property.
2. Create a Web data stream for `https://nexgenbinary.com/`.
3. Copy the Measurement ID beginning with `G-`.
4. In GitHub open `jooshondeh/site-public`.
5. Go to **Settings → Secrets and variables → Actions → Variables**.
6. Create a repository variable:

   - Name: `GA4_MEASUREMENT_ID`
   - Value: the real `G-` Measurement ID

7. Open **Actions**, choose the production Pages workflow, and select **Run workflow**.

The workflow safely writes the ID into the deployment artifact. The ID is not a
secret; using a repository variable avoids repeated file edits.

## Where to view the information

Sign in to Google Analytics and open the NexGen Binary property:

- **Reports → Realtime**: verify visits and events within minutes.
- **Reports → Acquisition**: traffic sources, search, direct, referrals, campaigns.
- **Reports → Engagement → Pages and screens**: page and section engagement.
- **Reports → Engagement → Events**: calls, emails, bookings, leads, and scroll depth.
- **Explore**: build custom funnels and comparisons.

Recommended events to mark as key events in **Admin → Events / Key events**:

- `generate_lead`
- `click_to_call`
- `booking_click`
- `email_click`

Additional events included:

- `google_business_click`
- `contact_form_start`
- `contact_form_error`
- `section_view`
- `scroll_depth`
- `web_vital`

Analytics loads only after consent and does not send contact-form values,
message contents, names, email addresses, practice names, or hCaptcha responses.
