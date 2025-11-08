# NexGen Binary LLC - Under Construction Page

This repository hosts a secure **Under Construction** placeholder for NexGen Binary LLC.

## How to use

1. Upload these files to a new **public** GitHub repository.
2. Go to **Settings → Pages → Source: Deploy from a branch → Branch: `main` → `/ (root)` → Save**.
3. (Optional) Connect a custom domain in **Settings → Pages → Custom domain**.
4. In your DNS (Microsoft 365 / GoDaddy), add:
   - `CNAME` for `www` → `YOUR-USERNAME.github.io`
   - `A` records for `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
5. After your main site is ready, replace `index.html` with your real content.

## Security & Privacy
- Includes meta tags: `noindex, nofollow, noarchive, nosnippet` to prevent indexing.
- Additional headers: `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, and `Permissions-Policy` for protection.
- `robots.txt` blocks all crawlers until ready to go live.

## Notes
- Keep this repo **public** if using free GitHub Pages. Private Pages require a paid GitHub plan.
