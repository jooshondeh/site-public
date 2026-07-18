# Google Analytics setup and access

The website is configured with GA4 Measurement ID:

    G-YY6Q8RTE7R

No GitHub Actions variable is required.

## Consent behavior

- The Google tag loads with analytics storage denied.
- A visitor can select Allow analytics or Decline.
- Closing the notice with X is treated as Decline.
- Contact-form contents and entered personal details are not sent to Analytics.
- Visitors can reopen the choice through Analytics settings in the footer.
- Global Privacy Control and Do Not Track are respected.

## View the data

Open Google Analytics and select the NexGen Binary property.

- Reports > Realtime: current users and immediate testing
- Reports > Acquisition: traffic sources
- Reports > Engagement > Pages and screens: page performance
- Reports > Engagement > Events: calls, email, bookings, and leads
- Explore: custom reports and funnels

Recommended key events:

- generate_lead
- click_to_call
- booking_click
- email_click
