# NexGen Binary — blue-brand website update

Release date: November 25, 2026  
Build: `production-2026-11-25-v9-blue-brand`  
Shared asset version: `20261125brand9`

## Outcome

This release applies the supplied NexGen Binary identity throughout the existing GitHub Pages website, replaces the orange brand accents with a coordinated blue palette, and repairs the specific accessibility and responsive defects found during review. It remains a static HTML/CSS/JavaScript site and uses the existing GitHub Actions workflow.

The original uploaded ZIP was checked against the live homepage, all four secondary HTML pages, the stylesheet, JavaScript and main logo. All eight checked files matched byte-for-byte by SHA-256. The audit therefore began from the deployed release, rather than an unrelated design.

## Logo and visual decisions

The main `nexgenbinary-logo.png` is an exact copy of the uploaded 960×396 PNG. Its pixels and transparency have not been altered. All eleven header/footer/error-page image instances use the correct intrinsic dimensions. The full wordmark now occupies approximately 216px in the desktop header and 180–204px in phone/tablet layouts; the duplicate typed company name was removed from the header. The existing company identity, tagline in the site metadata, business content, service plans, address, hours and contact information are retained.

The palette is derived from the supplied artwork:

| Use | Color | Reason |
| --- | --- | --- |
| Primary buttons, links and brand details | `#144681` | Exact dark logo blue; strong readability with white text |
| Decorative accents and hero CTA | `#6099D8` | Exact light logo blue; paired with dark text where interactive |
| Hero/footer and strong contrast areas | `#102B49` | Deep navy within the same family |
| Hover on primary buttons | `#0D4076` | A darker related blue |
| Light panels | `#E8F1FC` / `#F1F6FC` | Quiet separation without introducing a competing accent |

White text on the main blue is approximately **9.45:1**. Navy text on the light-blue hero CTA is approximately **4.81:1**. The lighter logo blue is not used as a background for ordinary white button text, because that combination is only about 2.98:1. W3C's normal-text reference threshold is 4.5:1, with a separate 3:1 threshold for large text. These selected color measurements do not constitute certification of the whole website.

Orange has been removed from primary buttons, hover icons, plan checks, active navigation, keyboard outlines, footer edges/links, back-to-top controls, privacy reminders, legal callouts and confirmation graphics. Error red and success green retain their semantic roles. Google, LinkedIn and Facebook icons retain their own brand colors.

The SVG/ICO/PNG favicons and Apple touch icon now use the symbol from the new artwork, which remains recognizable at small sizes. The 1200×630 social-preview image also uses the new logo and blue hierarchy. All shared assets have a consistent new cache version in the five HTML pages. Existing social sites may retain their own preview cache until refreshed by that service.

## Responsive and accessibility repairs

- Header logo proportions are preserved; the mobile logo is no longer squeezed into a 68px slot.
- Phone headings, card spacing and contact text reflow without horizontal overflow at narrow widths.
- Long email addresses and legal links can wrap within their cards.
- The mobile menu is limited to available viewport height and has its own vertical scrolling. Its contents align from the top, so lower links remain reachable. Scrolling a menu item into view no longer closes the menu prematurely.
- Menu button labels track the expanded state. Escape closes the menu and returns keyboard focus. The active section is exposed with `aria-current="location"`.
- When scripts are disabled, navigation remains visible and usable; it is not left behind a nonfunctional menu button.
- The actual sticky-header height is measured, so anchor offsets remain accurate as the layout changes.
- The message field's missing privacy-description ID has been repaired, and the privacy reminder spans both form columns.
- Booking and success overlays use native dialogs where supported, with background interaction blocked by the browser, visible close controls and return-focus handling. A fallback remains for older implementations.
- Booking controls are at least 44px. Small-screen booking notes span the full dialog width, and a clearly labeled external-booking button remains available.
- Focus outlines are readable on both light and dark sections. Forced-color overrides, reduced motion and safe-area allowances are included.
- Decorative hover movement is suppressed for touch/coarse pointers and reduced-motion preferences.

## Functional repairs

The 404 page now uses root-relative site assets and recovery links. This fixes the common case where a missing URL several folders deep would otherwise try to load its CSS and logo from that nonexistent folder.

Malformed percent-encoded URL fragments no longer throw an exception that stops the entire shared script. Modified booking clicks (such as Ctrl/Cmd-click) retain their normal browser behavior.

The contact form still uses the existing Formspree endpoint and public hCaptcha site key. CAPTCHA size is selected from the actual available form width. Verification loading has a 15-second timeout and a visible retry control. Form submission has an in-flight guard, a disabled/busy state, a nonempty verification-token requirement and a 20-second request deadline. Errors retain the entered message and restore controls. A timed-out request explicitly says delivery could not be confirmed, because a timeout alone cannot prove that the provider did not receive it.

## What was verified

The final source validator passed **5 HTML pages, 14 native telephone links, 11 logo instances, 72 local anchors and 13 ARIA references**, together with assets, cache versions, structured metadata, business hours, integration hooks and CSS custom properties. JavaScript syntax passed. A copy of the original repository overlaid with exactly the replacement package also passed. The existing deployment allowlist was reproduced and its clean output passed the workflow's `--clean` check.

Chrome/Chromium browser testing covered 34 page/viewport combinations. The homepage was measured at 320×568, 360×800, 390×844, 414×896, 667×375, 768×1024, 1024×768, 1280×800, 1440×900 and 1920×1080. Booking, Privacy, Terms and 404 were each measured at six representative sizes (320, 390, 667, 768, 1024 and 1440px widths). No horizontal overflow or overflowing content element was found in those checks. The browser's desktop scrollbars reduced usable width by 15px, making the narrowest content area 305px.

Interaction checks covered menu scrolling and Escape, pointer/keyboard section navigation, a 320px no-script navigation fallback, dialog open/close/focus behavior, the malformed-fragment case and narrow contact text. An isolated local test harness, with outgoing connections and form posts disabled, exercised empty-field errors, missing verification, simulated HTTP 503, simulated success and a stalled request. The test harness is excluded from the delivered files.

## What still needs a production check

This release is locally validated and ready for upload; it has not been committed or deployed. Responsive viewport tests are not a substitute for every physical device or browser engine. Safari/Firefox, real iOS/Android, screen-reader operation and actual browser zoom were not executed. Reduced motion, forced colors and device safe areas were reviewed in source.

The embedded Microsoft calendar did not render in the local preview. The exact existing URL returned an empty HTTP 417 response through an envoy server when probed, which does not establish that the URL or Microsoft's frame policy is wrong. The existing booking URL is retained and a separate-tab fallback is clearly available. After deployment, open the live calendar once. If the embed also fails there, compare the iframe code in Microsoft Bookings → Booking page → Embed in Your Website and check the booking page's external visitor access.

No real contact message, CAPTCHA completion or appointment was sent during the review. After deployment, verify the live hCaptcha and submit one clearly identified test inquiry from your own browser, then confirm it arrives at the configured mailbox. A successful browser message alone does not prove inbox delivery.

## Upload and rollback

Upload every file and folder inside the package's `UPLOAD_TO_GITHUB` directory into the root of the existing `jooshondeh/site-public` repository, preserving paths. Include `scripts/validate_site.py`: the existing workflow checks the build/cache markers and would reject new HTML with the old validator. Do not upload the wrapper directory as a nested website folder.

Merge the update into `main` (or commit to `main` if that is your established workflow). The existing “Deploy production site to GitHub Pages” Action publishes pushes to that branch. Wait for the green deployment result, then hard-refresh the site. Existing GitHub Pages and DNS settings continue to apply; this release requires no DNS or publishing-source change.

For rollback, revert the update commit/merged PR or restore the matching original files as one consistent set. Keep the original ZIP as an additional backup. No existing files need to be deleted for this update.

For an optional post-deployment read-only check, run `python3 scripts/check_live_site.py`. It checks the new build and a nested missing URL without sending forms or making bookings.

## Primary references

- [W3C text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [W3C reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)
- [MDN native modal dialogs](https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/showModal)
- [GitHub file/folder uploads](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)
- [GitHub Pages publishing](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Microsoft Bookings sharing/embedding](https://learn.microsoft.com/en-us/microsoft-365/bookings/share-shared-bookings-page?view=o365-worldwide)
