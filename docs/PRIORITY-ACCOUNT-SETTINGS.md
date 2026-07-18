# External account settings

These settings cannot be changed by repository files.

## Formspree

In the Formspree project/form settings, restrict submissions to the bare domain:

```
nexgenbinary.com
```

Then submit a real production test and confirm delivery to
`info@nexgenbinary.com`.

## hCaptcha

For site key `267e959c-42c0-45b2-a4d2-45621dbc4f28`, enable domain
allowlisting and add:

```
nexgenbinary.com
```

The website now loads hCaptcha only when the contact form approaches the
viewport or the visitor interacts with the form.

## GitHub Pages

Set the source to GitHub Actions, configure `nexgenbinary.com` as the custom
domain, and enable HTTPS. The source repository does not need dot-prefixed
production files because the workflow generates them.
