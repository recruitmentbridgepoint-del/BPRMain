# Bridgepoint Recruitment website

Static site served by a Cloudflare Worker. The Worker also emails form submissions and redirects old Wix URLs.

## Folders
- `public/` — the website (homepage, jobs, privacy, terms, thanks, images, sitemap, robots)
- `data/jobs.json` — job listings; edit this to add, change or remove roles
- `src/worker.js` — form handling (brief, apply, register) and redirects
- `build_jobs.py`, `build_pages.py`, `seo.py` — regenerate pages after editing jobs

## After editing jobs
```
python3 build_jobs.py && python3 build_pages.py && python3 seo.py
```

## Settings to check before launch
- `seo.py`: `SITE` (final domain) and `POSTED` (listing date)
- `src/worker.js`: `TO` (form recipient) and `FROM` (sender address on your domain)
- Email: the `send_email` binding needs Cloudflare Email set up for the domain, and the recipient address verified
