# Analytics account cleanup and verification

Website Measurement ID:

    G-YY6Q8RTE7R

Keep only the property whose Web data stream shows exactly that Measurement ID and the URL `https://nexgenbinary.com`.

From the screenshots, the likely working selection is:

- Account: NexGen Binary Website
- Account ID: 401570499
- Selected property ID: 546143293

Confirm the Measurement ID before deleting anything.

The crossed-out entries appear to already be in Trash:

- Account: NexGen Binary LLC
- Account ID: 401590144
- Property ID: 546148849

Leave them in Trash only if neither contains the active `G-YY6Q8RTE7R` stream. Google Analytics keeps trashed accounts and properties recoverable for 35 days.

## Realtime test

1. Open the selected property.
2. Go to Admin > Data streams and confirm `G-YY6Q8RTE7R`.
3. Open `https://nexgenbinary.com` in an Incognito/InPrivate window.
4. Disable ad blockers for the test.
5. Select Allow analytics.
6. Keep the site open and navigate through sections.
7. Check Reports > Realtime after several minutes.
8. In browser developer tools, Network should show `gtag/js?id=G-YY6Q8RTE7R` and requests containing `g/collect`.
