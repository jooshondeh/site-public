# NexGen Binary Website, Google Business, Bookings, and Google Voice Guide

**Audit date:** July 24, 2026  
**Website:** NexGenBinary.com  
**Release:** production-2026-07-24-v7-compatibility

## 1. Executive result

The production website source is structurally sound and does not require a redesign. The compatibility release applies conservative browser and mobile fixes without changing the visual design or business content.

Validated items:

- Five HTML documents parse correctly.
- All local assets and internal links resolve in the packaged site.
- JavaScript passes syntax validation.
- CSS parses without errors.
- No duplicate HTML IDs were found.
- Canonical URLs, robots.txt, sitemap.xml, Open Graph metadata, social preview image, and structured data are present.
- Navigation has desktop and mobile states.
- Form validation, hCaptcha lazy loading, Microsoft Bookings integration, native phone links, and legal pages are present.
- Focus styling, reduced-motion handling, responsive images, mobile breakpoints, and touch-friendly controls are included.

### Compatibility corrections in v7

1. Added `-webkit-backdrop-filter` before `backdrop-filter` for Safari/WebKit.
2. Added `100vh` fallbacks before `100dvh` for browsers that do not understand dynamic viewport units.
3. Added legacy `MediaQueryList.addListener()` fallback for older Safari/WebView environments.
4. Kept the mobile navigation control at a minimum 44 × 44 CSS pixels.
5. Updated cache markers so browsers retrieve the corrected CSS and JavaScript.
6. Updated the sitemap modification date and security.txt expiration date.
7. Updated local and live validation scripts for the new production build.

## 2. Files to upload

### Safest method: full replacement

Upload the complete contents of `NexGenBinary_Production_v7_Compatibility_Full.zip` to the repository root, preserving all folders. Replace matching files. Do not upload the enclosing ZIP folder itself.

### Minimum replacement method

Replace these paths from `NexGenBinary_v7_Compatibility_Replacement_Files.zip`:

- `.github/workflows/static.yml`
- `404.html`
- `assets/site.css`
- `assets/site.js`
- `book/index.html`
- `index.html`
- `privacy/index.html`
- `scripts/check_live_site.py`
- `scripts/validate_site.py`
- `sitemap.xml`
- `terms/index.html`

## 3. Deployment steps

1. Download a backup ZIP of the current repository.
2. Open the repository’s default production branch.
3. Confirm there is only one active deployment workflow under `.github/workflows/` and that it is `static.yml`.
4. Upload the replacement files while preserving their directory paths.
5. Commit with the message: `Deploy v7 compatibility and cache refresh`.
6. Open the repository’s Actions page.
7. Open the newest Pages deployment run.
8. Confirm the validation, artifact upload, and deployment jobs complete successfully.
9. Open the public site in a private browser window.
10. Hard refresh once: Ctrl+Shift+R on Windows or Command+Shift+R on macOS.
11. Test the homepage, booking page, privacy page, terms page, contact form, phone links, mobile menu, and Google profile icon.
12. View page source and confirm the build marker contains `production-2026-07-24-v7-compatibility`.

## 4. Post-deployment compatibility test matrix

Test at minimum:

- Chrome on Windows: 1440, 1024, 768, 390, and 320 CSS-pixel widths.
- Edge on Windows: desktop and mobile device emulation.
- Firefox on Windows or macOS: desktop and 390 CSS-pixel width.
- Safari on iPhone: portrait and landscape.
- Safari on iPad: portrait and landscape.
- Chrome on Android: portrait and landscape.
- macOS Safari: desktop, keyboard navigation, and reduced-motion mode.

For every test confirm:

- No horizontal scrolling.
- Header logo loads.
- Desktop navigation changes to the menu button at the intended breakpoint.
- Menu opens, closes, and does not cover inaccessible content.
- Buttons are easy to tap.
- Booking modal fits the viewport and can be closed with the button and Escape key.
- Contact form shows validation messages and hCaptcha loads.
- Phone and email links open the correct applications.
- Privacy, terms, booking, and 404 pages retain the same header/footer styling.
- Text remains readable at 200% browser zoom.
- Tab navigation has a visible focus indicator.

## 5. Google Business Profile: verification and visibility

An ordinary public profile does not always display a visible “verified” label. Verification is principally checked from the owner account. Public visibility must be tested separately.

### Check owner-side verification

1. Sign into the Google account that created or claimed the profile.
2. Search Google for `NexGen Binary LLC Glen Allen` or `my business`.
3. Open the management panel for NexGen Binary.
4. Look for `Get verified`, `Verification needed`, or another verification prompt.
5. If a verification prompt is present, complete the method Google offers. Google chooses the available method; it may require video, phone, text, email, or another method.
6. Open `Edit profile` and confirm the business name, primary category, phone, website, hours, service area, and address behavior.
7. Open the edit-status area and resolve any item marked pending, rejected, or not approved.

### Open the profile as the public sees it

1. In Chrome, open a Guest profile or Incognito window.
2. Confirm the managing Google account is not signed in.
3. Search the exact business name plus `Glen Allen VA`.
4. Search the exact office phone number.
5. Repeat both searches in Google Maps.
6. Check whether the business name, category, website, phone, hours, service area, and logo are visible.
7. From the owner panel, use `Share profile`, copy the public link, and open it in the private window.
8. Repeat on a mobile device using a private browser tab and the Google Maps app signed out of the owner account.

### Critical address decision

Use only one of these configurations:

**Service-area business — recommended when customers do not visit the address**

1. Open `Edit profile`.
2. Open `Location`.
3. Remove or hide the street address from customers.
4. Keep the real address privately for verification when Google requests it.
5. Add accurate service areas by city, postal code, or region.
6. Do not use a radius.
7. Keep the total service area realistic and normally within roughly a two-hour drive of the operating base.

**Hybrid/storefront business — only when the location qualifies**

Keep the address public only when NexGen Binary has permanent on-site signage, staff is present during listed hours, and customers can actually visit and receive service there.

A mailbox, virtual office, coworking address without staffed customer access, or another company’s suite should not be presented as a storefront.

## 6. Add or repair business hours

Use regular `Business hours`, not `More hours`, for the main schedule.

1. Sign into the managing account.
2. Open the Business Profile.
3. Select `Edit profile`.
4. Select `Hours`, then the edit control for Business hours.
5. Choose `Open with main hours`.
6. Check Monday through Saturday.
7. Enter `9:00 AM` opening and `5:00 PM` closing for each selected day.
8. Leave Sunday unchecked or mark it closed.
9. Save.
10. Open the edit-status view and confirm the hours are accepted or pending review.
11. Open the profile in a private window and Google Maps to confirm public display.
12. Add special hours for holidays rather than changing the regular weekly schedule.

When the owner panel still says “business hours are missing” after the hours are saved:

1. Confirm the primary category is selected.
2. Confirm the profile is verified.
3. Confirm the profile is not marked temporarily closed, permanently closed, or not yet open.
4. Reopen Hours, choose `Open with no main hours`, save, then re-enter the main hours once. Use this reset only when the saved schedule is visibly stuck.
5. Check whether an edit is pending or rejected.
6. Capture screenshots and contact Google Business Profile support if the owner warning remains after the edit is approved.

## 7. Upload the logo successfully

Use `NexGenBinary_GoogleBusiness_Mark_720.png` first. Its simplified symbol remains readable in Google’s circular crop. Use `NexGenBinary_GoogleBusiness_Full_720.png` as a secondary brand image or alternative logo test.

1. Confirm the profile is verified.
2. Confirm name, category, phone, main hours, and either a qualifying location or correct service-area setup are complete.
3. Open the profile in Google Search or Maps.
4. Select `Photos`.
5. Select `Add a logo` or `Change logo`.
6. Upload the 720 × 720 PNG mark.
7. Reposition the crop so the complete mark remains inside the circular safe area.
8. Save.
9. Open Photos and check the media status.
10. Wait through Google’s review. A photo can be Pending, Not approved, or Live.
11. Check again in a signed-out/private view after it becomes Live.
12. If rejected, remove the rejected upload and retry the full-wordmark file once; do not repeatedly upload duplicates while one is pending.

## 8. Social media priority

Create pages only where the company can maintain accurate information and publish useful content.

1. **LinkedIn company page — highest priority.** Best fit for a B2B technology provider targeting practice owners, office managers, dentists, vendors, and referral partners.
2. **Facebook business page — second.** Useful for local legitimacy, community visibility, reviews, and another consistent business citation.
3. **YouTube — third.** Add when the company can publish helpful demonstrations, cybersecurity explainers, Microsoft 365 tips, and dental IT guidance.
4. **Instagram — optional fourth.** Useful for visual project highlights and team updates, but normally lower purchase intent for managed IT.

For each page:

1. Use `NexGen Binary LLC` consistently.
2. Use the same logo, phone, website, service area, hours, and description.
3. Link back to the website.
4. Add the live social URL to Google Business Profile under `Edit profile` > `Contact` > `Social profiles`, when that feature is available.
5. After the pages are live, add their URLs to the website structured data `sameAs` array.
6. Publish at least one useful post before publicly promoting the page.

## 9. Microsoft Bookings recommendation

Twenty minutes is appropriate for an introductory qualification call, not for detailed technical troubleshooting or a full environment assessment.

Recommended service:

- Service name: `20-Minute Dental IT Consultation`
- Duration: 20 minutes
- Post-meeting buffer: 10 minutes
- Booking interval: 30 minutes
- Location: Microsoft Teams online meeting
- Minimum lead time: 4 business hours when the calendar is actively monitored; otherwise 24 hours
- Maximum lead time: 60 days
- Cancellation/reschedule cutoff: 4 hours
- Staff selection: Off; assign automatically for a small team
- Customer management: Allow rescheduling and cancellation
- Business notification: On for every created or changed booking
- Customer reminders: 24 hours and 1 hour before
- Follow-up: 2 hours after
- SMS: Optional and only when licensed; one reminder is enough

Recommended required customer fields:

- Name
- Email
- Phone
- Practice or organization name
- City
- Number of locations

Optional field:

- `What would you like to discuss?`

Place this directly above or below the optional notes field:

> Please do not include patient names, treatment details, insurance information, or other protected health information in this form.

Create a separate 45- or 60-minute discovery meeting for prospects who need deeper technical review after the introductory call.

### Configure Bookings

1. Open Microsoft Bookings.
2. Open the shared booking page for NexGen Binary.
3. Open `Services`.
4. Edit the consultation service.
5. Set the service name, description, location, duration, buffer, customer fields, assigned staff, and availability.
6. Enable the Teams meeting option.
7. Open the service’s Notifications page.
8. Add the confirmation text.
9. Add reminders for 24 hours and 1 hour before the meeting.
10. Add a follow-up for 2 hours after the meeting.
11. Save the service.
12. Open `Booking page` and set the time increment, minimum lead time, maximum lead time, and business notification option.
13. Save and publish.
14. Book a test appointment with an external email address.
15. Verify the customer confirmation, staff notification, calendar event, Teams link, time zone, manage-booking link, reminders, and cancellation flow.

## 10. Google Voice account type and Upgrade button

The Upgrade button alone does not prove that the number is personal. Check the account message:

1. Open Google Voice on a computer.
2. Open `Settings`.
3. Open `Account`.
4. Read the account-status text:
   - `This account is managed by your Google Workspace administrator` means it is a managed Workspace Voice account.
   - `Manage my account` means it is a paid single-user standalone Voice account.
   - Neither message normally means a no-charge personal/unmanaged account.

Identity verification with a personal ID is an identity or number-transfer control. It does not decide whether the plan is a personal or managed business subscription.

### Recommended business setup

For multiple NexGen Binary users sharing a main number, use Google Voice Standard as a Google Workspace add-on. Standalone Voice Standard is still one user and does not provide multi-user ring groups or call delegation.

1. In Google Admin, purchase or confirm Google Voice Standard for Workspace.
2. Assign a Voice license to each team member who must answer business calls.
3. Configure each user’s location and emergency service address.
4. Assign each licensed user a direct Voice number as needed.
5. Transfer the current consumer number into the organization if it is still held by a personal account.
6. In the personal Voice account, open Settings > Account > Transfer a number.
7. Select Get started and submit the current number and the destination corporate account email.
8. In Google Admin, accept the transfer request.
9. Create a ring group for the public main number.
10. Add only the staff members responsible for incoming calls.
11. Select simultaneous ringing for the primary group, with overflow or voicemail after an appropriate timeout.
12. Configure business-hours and after-hours behavior.
13. Test inbound calls, outbound caller ID, unanswered calls, voicemail delivery, and emergency-address configuration.

## 11. Delegates versus ring groups

Do not add every user as a delegate by default.

- Use a **ring group** when several people should answer calls to one public company number.
- Use **call delegation** only when one person must place, receive, or manage calls on behalf of another specific user, such as an executive assistant arrangement.
- Give access only to trained staff with a legitimate operational need.
- Review membership whenever someone changes roles or leaves the business.

## 12. Personal and business numbers in the mobile app

The Google Voice mobile app can contain more than one Google account. Switch accounts from the profile picture. A personal Voice number and a business Voice number can therefore be used in the same app, but they remain separate accounts and inboxes.

The device’s cellular phone number can be linked to only one Voice account at a time. Prefer `Use carrier only` or the device-number option only where necessary; use Wi-Fi/mobile data in the Voice app for the other account.

After adding both accounts:

1. Confirm the active account before placing a call or sending a text.
2. Set distinct notification behavior where the operating system permits it.
3. Place a test outbound call from each account and confirm the caller ID.
4. Call each Voice number and confirm the correct account rings.

## 13. Voicemail and automated voice

### Regular user voicemail

Basic/personal Voice and individual Voice accounts record the greeting through the microphone; they do not provide an in-place voice picker for the normal user voicemail greeting.

1. Open Voice on a computer.
2. Open Settings.
3. Open Voicemail.
4. Under Active greeting, select Record a greeting.
5. Record, stop, review, and save.
6. Name the greeting clearly, such as `Main business voicemail July 2026`.
7. Open Manage all greetings and set it active.
8. Call the number from an outside phone and confirm audio quality.

### Text-to-speech business greeting

Google Voice Standard or Premier auto attendants support text-to-speech and uploaded audio.

1. In Google Admin, open Apps > Google Workspace > Google Voice.
2. Open Auto attendants.
3. Create or edit the company auto attendant.
4. Under Initial greeting, add a welcome message.
5. Choose text-to-speech.
6. Enter the greeting.
7. Open the Default voice setting.
8. Select English (United States), a clear professional voice, and normal or slightly slower speed.
9. Preview it, then save.
10. Configure call handling to transfer to the ring group during business hours and voicemail after hours.
11. Test from outside the organization.

## 14. Searchability and trust priorities

### Highest priority

1. Resolve Google Business verification and correct the storefront versus service-area configuration.
2. Confirm the public listing can be found by exact name, phone, and website.
3. Keep business name, phone, website, hours, and service area identical on the website, Google, LinkedIn, Facebook, Microsoft, and directories.
4. Submit and verify the website in Google Search Console and Bing Webmaster Tools.
5. Submit the sitemap and inspect the homepage, privacy page, and terms page.
6. Ask real clients for honest Google reviews after successful service; never offer incentives or use review gating.

### Content expansion

7. Add a dedicated `Dental IT Services` page.
8. Add separate pages for cybersecurity, Microsoft 365, network management, backup/disaster recovery, VoIP, cameras, and website services.
9. Create location/service-area pages only where the company genuinely serves customers and can provide unique local information; avoid duplicate city pages.
10. Add an FAQ section answering buyer questions such as response times, HIPAA responsibilities, onboarding, support hours, cloud migrations, backups, and vendor coordination.
11. Publish useful articles based on real customer questions rather than generic AI-generated search pages.
12. Add Organization and Service schema to new service pages, and add valid social profile URLs to `sameAs` after those pages are live.

### Technical maintenance

13. Keep one production deployment workflow.
14. Keep third-party scripts minimal.
15. Re-test Formspree, hCaptcha, and Bookings monthly.
16. Review broken links, 404s, Search Console coverage, and Core Web Vitals monthly.
17. Update special business hours before holidays.
18. Refresh the security.txt expiration annually.
19. Maintain verified backups of the repository and DNS records.
20. Run the packaged validation scripts before every deployment.

## 15. Recommended scripts

### Booking confirmation

**Subject:** Your NexGen Binary consultation is confirmed

Hello [Customer name],

Thank you for scheduling a 20-minute introductory consultation with NexGen Binary.

During the call, we’ll learn about your dental practice, current technology environment, and priorities, then outline practical next steps. This appointment is intended for an initial conversation and is not an emergency support session.

Please do not include patient names, treatment information, insurance details, or other protected health information in booking notes, email, or chat.

Use the Manage booking link in this message to reschedule or cancel. Your online meeting link is included below.

We look forward to speaking with you.

NexGen Binary LLC  
(804) 460-9640  
info@nexgenbinary.com

### 24-hour reminder

**Subject:** Reminder: Your NexGen Binary consultation is tomorrow

Hello [Customer name],

This is a reminder of your 20-minute NexGen Binary consultation on [date] at [time] Eastern. Use the meeting link below to join.

Use the Manage booking link to reschedule or cancel. Please do not send patient information or other protected health information in email, chat, or booking notes.

NexGen Binary LLC

### Voicemail greeting

Thank you for calling NexGen Binary, Virginia’s trusted IT partner for dental practices. We’re unable to answer right now. Please leave your name, practice name, callback number, and a brief description of how we can help. Please do not leave patient information or other protected health information. We’ll return your call within one business day. Managed clients with an urgent support issue should use the support contact listed in their service agreement.

### Live phone answer

NexGen Binary, this is [Name]. How may I help you?

A slightly warmer version:

Thank you for calling NexGen Binary. This is [Name]. How can I help?
