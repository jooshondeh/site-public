# Under Construction Placeholder Site

This repository is a minimal, production-ready **Under Construction** page for GitHub Pages.

## How to use

1. Upload these files to a new **public** GitHub repository.
2. Go to **Settings → Pages → Source: Deploy from a branch → Branch: `main` → `/ (root)` → Save**.
3. (Optional) Connect a custom domain in **Settings → Pages → Custom domain**.
4. In your DNS (Microsoft 365 / GoDaddy), add:
   - `CNAME` for `www` → `YOUR-USERNAME.github.io`
   - `A` records for `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
5. After your main site is ready, replace `index.html` with your real content.

## Notes
- `robots.txt` and `<meta name="robots" content="noindex,nofollow">` block indexing while you build. Remove them when going live.
- Keep this repo **public** if using free GitHub Pages. Private Pages requires a paid GitHub plan.
