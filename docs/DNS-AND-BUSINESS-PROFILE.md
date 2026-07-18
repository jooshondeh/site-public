# DNS and Google Business review

## DNS result

The Microsoft 365 DNS export shows:

- Four GitHub Pages A records at the apex
- `www` CNAME to `jooshondeh.github.io`
- Microsoft 365 MX and SPF
- Autodiscover
- Two DKIM selectors
- Microsoft 365 nameservers

No conflicting website A or `www` records are visible in the supplied export.

## Recommended DNS addition

A DMARC TXT record is not visible in the supplied DNS export. Use a staged DMARC
rollout after creating a reporting mailbox or DMARC reporting service.

Example monitoring record:

    Type: TXT
    Name: _dmarc
    Value: v=DMARC1; p=none; pct=100; rua=mailto:dmarc@nexgenbinary.com

Do not use that reporting address until it exists.

## Google Business Profile ID

Business Profile ID:

    5708438775538878600

This ID is intended for Google support and profile administration. It is not a
public customer link and is not used as the footer icon destination.

The website correctly keeps this customer-facing link:

    https://share.google/UWWubeCa8CN4sffAM
