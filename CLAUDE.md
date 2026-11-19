# Luxury Phuket — project context for Claude

Read this first. It is the handover from the cloud session that built the site (Nov 2026).
Talk to the owner **in Russian**, short and concrete. The owner is not a developer: do the work yourself,
give click-by-click steps only for things that need their accounts (Google, Cloudflare dashboard, Telegram).

## What this is
- **Site:** villa rentals, property for sale and new projects on Phuket. Brand **Luxury Phuket**.
- **Live:** https://luxuryphuket.net (Cloudflare Workers, auto-deploy from `main`). `www.` also served (canonical → apex).
- **Old copy:** https://jokerfrombali.github.io/thaivillas/ (GitHub Pages, same repo, kept `noindex`).
- **Repo:** `jokerfrombali/thaivillas` (public — never commit secrets, tokens or the owner's private email).
- **Contacts on the site:** WhatsApp/phone `+66 81 123 7388` (`tools/thai/thv.py`: `WA_NUM`, `PHONE`; `thb-enquiry.js`: `WA`).
  Email: `hello@luxuryphuket.net` (Zoho Mail free, MX/SPF/DKIM in Cloudflare DNS, verified 17.11.2026).
- Content language: English. Listings come from getyourphuket.com (EN) and indreamsphuket.com (EN version of indreamsphuket.ru).

## Numbers (current data)
`data/villas.json` 1,904 rentals · `data/sale.json` 1,230 for sale · `data/projects.json` 583 new projects (~3,717 listings, ~120k photos).
Site output ~600 MB, ~7,600 files (Cloudflare limits: 20k files, 25 MB/file; GitHub Pages: 1 GB).

## How the site is built (static generator, Python)
Pages are **generated** — do not hand-edit HTML under `villa/`, `sale/`, `projects/`, `villas/`, `property-rental/`,
`monthly-rental/`, `vip/`, `index.html` etc. Edit the generators in `tools/thai/` and rebuild.

```
THAI_TPL=<path to jokerfrombali/thebalihost checkout> python3 -I tools/thai/build_all.py --base /thaivillas
```
- `--base /thaivillas` is required: the repo copy is built for GitHub Pages under `/thaivillas/`
  (`build_all.py` unprefixes data/js/css first, runs every generator, compiles Tailwind, then prefixes paths).
- `THAI_TPL` = a checkout of the **private** repo `jokerfrombali/thebalihost` (the Bali site whose villa-page
  design is the template; read-only, never modify it). A shallow clone with `--filter=blob:limit=2m` is enough.
- Tailwind step (`tools/perf/build-tailwind.sh`) needs Node 18+ and npm (installs tailwindcss@3 on first run).
- Full build takes ~10 min. Generators assert on template leftovers ("Host", "Sanur"…) — real listing text is exempt.

Generators (`tools/thai/`):
- `thv.py` — shared shell: brand, contacts, nav (`NAV_LINKS`), footer, logo (`LOCKUP`, `LOGO_CSS`: gold roof SVG +
  LUXURY/PHUKET with thin black outline), cards (`prop_card`, `acard`, `card_meta`), `price_label`, `write()` (injects logo CSS).
  Loads `VILLAS`, `SALE`, `PROJECTS`, `AREAS`.
- `build_home.py` (home, 404, /saved/, favicon), `build_areas.py` (catalogue /property-rental/, /villas/ hubs, beaches;
  cards lazy-load: 48 in HTML, rest from `data/cards-<deal>.json`; also writes `data/map-villas.json` for the map),
  `build_villas.py` (every listing page + `/gallery/`; sale/project pages use `buy_mode()` — no dates/guests,
  WhatsApp "Request details" / "Book a viewing"; shared CSS/JS moved to `villa/ui/x/<hash>`),
  `build_sale.py` (/sale/, /sale/<dest>/, /projects/), `build_monthly.py`, `build_vip.py`, `build_info.py`.
- `import_listings.py` — converts importer catalogs into `data/villas.json` / `sale.json` / `projects.json`
  (drops site boilerplate, picks prices, Phuket sub-areas, project ranges: `bedroomsRange`, `areaRange`, `completion`, `ownership`).

## Photos (not in this repo)
Compressed WebP (1280 px, q72) live in GitHub Pages repos `jokerfrombali/thaivillas-media-01` … `-09`
(≤900 MB each; `-10`…`-13` exist but are empty/unused). URL: `https://jokerfrombali.github.io/thaivillas-media-NN/<src>/<slug>/NN.webp`,
src `gyp` = getyourphuket, `ind` = indreams. Mapping listing → repo: `data/media-map.json`.
New photos: `tools/phuket-importer/media.py` (download+compress) → `shard_media.py` (assign repos, hard links)
→ `push_media.sh <repo dir>` (pushes in ~60–150 MB chunks). The owner must enable Pages on any new media repo.

## Importer (re-scrape sources)
`tools/phuket-importer/app.py` — `python3 app.py crawl getyourphuket|indreams-en|indreams [--no-photos]`,
web UI on :8090 (Docker: `run.ps1` / `run.sh`, port 8093). Output → `imports/` (git-ignored).
Supports `IMPORTER_CACHE=<dir>` (resumable), per-site URL rules in `SITES` (indreams paths are case-insensitive;
`/phuketpdfv2/` pages skipped). Then `import_listings.py --source gyp=<dir> --source ind=<dir> --media-root <media dir>`.

## Deploy: Cloudflare (luxuryphuket.net)
- Cloudflare Workers project **thaivillas**, connected to GitHub `main`: every push rebuilds and deploys (~3–5 min).
- `wrangler.jsonc`: build command `python3 tools/cloudflare_build.py`; assets `./dist`; custom domains
  `luxuryphuket.net` + `www.luxuryphuket.net` (DNS + certificates managed by Cloudflare); worker `src/worker.js`
  runs only for `/api/*`; `send_email` binding `LEADS`.
- `tools/cloudflare_build.py` copies the site to `dist/` **without** the `/thaivillas` prefix, removes `noindex`,
  adds `<link rel="canonical">` + `og:url` (https://luxuryphuket.net/...), keeps `gallery/`, `saved/`, 404 `noindex,follow`,
  writes `robots.txt`, `sitemap.xml` (~3,759 URLs), `_redirects` (/thaivillas/* → /*), `_headers`.
  Files skipped from dist: `tools/`, `src/`, `.git*`, `README.md`, `CLAUDE.md`, `wrangler.*`.

## Enquiries (leads)
- Booking form `thb-enquiry.js` POSTs JSON to `/api/enquiry` → `src/worker.js` sends it to **Telegram**
  (secrets `TG_BOT_TOKEN`, `TG_CHAT_ID` — comma-separated ids allowed) and/or email via Cloudflare Email Routing
  (secret `LEAD_TO`). Secrets are set in Cloudflare: Workers & Pages → thaivillas → Settings → Variables and Secrets.
- Not configured → 503 and the form falls back to WhatsApp (nothing is lost). Check:
  `curl -s -X POST https://luxuryphuket.net/api/enquiry -d '{"name":"test"}'` → `"not configured"` until secrets exist.
- Sale/project buttons and header/footer WhatsApp buttons go straight to WhatsApp, not through the form.
- Owner chose **Zoho Mail** for `hello@luxuryphuket.net` → do NOT enable Cloudflare Email Routing (MX conflict).

## Status / open tasks (owner's checklist)
Done: all listings live, logo, brand rename, light catalogues, sale/project pages, Cloudflare + domain + SSL,
indexing opened (robots, sitemap, canonical), Telegram/email lead endpoint.
Done 17.11.2026 (Google account of the project: luxuryphuketnet@gmail.com — NOT newlifeonbali@gmail.com):
- Search Console: domain property verified by TXT `google-site-verification=8o_zNr...` in Cloudflare DNS (keep it), sitemap submitted (3,759 URLs).
  "Request indexing" for main pages returned "try later" right after creation — retry.
- GA4: account "Luxury Phuket", stream luxuryphuket.net, **G-V4843CE7W2**, linked to Search Console. gtag + Consent Mode
  injected by `tools/cloudflare_build.py` (GA_HEAD, live site only); events: `thb-events.js` (whatsapp_click, phone_click,
  booking_open/submit) + `generate_lead` / `enquiry_whatsapp` in `thb-enquiry.js`.
- Cloudflare: Always Use HTTPS on; Redirect Rule www → apex (301, keeps path + query).
Also done 17–18.11.2026: Telegram leads + Zoho mail bridge (see "Telegram" below), hello@luxuryphuket.net on the site,
llms.txt, IndexNow, price facts in area/sale FAQ.
Open / next (19.11.2026):
- Google Business Profile "Luxury Phuket" created (service area Phuket, no address, luxuryphuketnet@gmail.com) — NOT verified:
  the owner works online, Google needs a real address. Finish when there is an office/coworking (business.google.com → Verify).
- Bing Webmaster: Microsoft blocked account creation — retry later (no VPN / from phone). Bing already gets URLs via IndexNow.
- Directories: FazWaz = owner listings only (leads go to FazWaz); Dot Property / Thailand-Property / Hipflat for agencies only via
  Proppit (paid, demo request); DDproperty paid. Owner not paying yet.
- Proposed next: own content — guide articles (monthly rent prices by area, can foreigners buy, Bang Tao vs Rawai) + FAQ page;
  Facebook/Instagram/Reddit by the owner (texts in tools/marketing/listing-kit.md); Russian version; retire github.io copy.
- Search Console: retry "Request indexing" for main pages.

## Working rules
- Commit to `main` (Cloudflare deploys it). Branch `real-listings` mirrors main (used for staged builds).
- Before pushing a rebuild, check a few pages in a browser (Playwright) and that `grep -c /thaivillas/ dist/index.html` is 0 after `cloudflare_build.py`.
- Never put tokens, passwords or the owner's private email in the repo (it is public). Use Cloudflare secrets.
- Keep the GitHub Pages copy `noindex`; only luxuryphuket.net is indexed.

## Telegram (done 17.11.2026)
Group "Luxury Phuket" (forum) id -1004370261657, bot = TG_BOT_TOKEN secret.
- Topic 3 "Заявки": `TG_CHAT_ID` secret = `-1004370261657:3` ("chat:topic"). Leads in Russian (`src/worker.js` leadText):
  booking form (/api/enquiry) + every WhatsApp click (/api/lead from `thb-bot.js`, injected on the live site by
  cloudflare_build.py). Source = first page of the visit (utm_source / referrer: ChatGPT, Google…), city/region/ISP/device.
- Topic 7 "Почта": `TG_MAIL_CHAT` var in wrangler.jsonc. `src/mail.js`: cron every minute reads Zoho Mail API
  (hello@luxuryphuket.net, Zoho Forever Free — API works) and posts new mail; Telegram Reply to that post is sent back
  from hello@ (Telegram webhook /api/tg/webhook, secret derived from the bot token). Zoho API client
  "Luxury Phuket Telegram Bridge" (api-console.zoho.com, luxuryphuketnet@gmail.com), secrets ZOHO_CLIENT_ID /
  ZOHO_CLIENT_SECRET; refresh token + state in KV `thaivillas-state` (binding STATE). Reconnect: delete KV key
  `zoho_refresh`, open https://luxuryphuket.net/api/zoho/connect.

## Building on Windows (Git Bash) — gotchas (18.11.2026)
- `export MSYS_NO_PATHCONV=1` or `--base /thaivillas` becomes `C:/Program Files/Git/thaivillas`.
- `python3` is a Store stub: put a `python3` shim first in PATH (tailwind script calls it).
- Python writes CRLF: after the build run `git diff --name-only -z | xargs -0 sed -i 's/\r$//'` (else ~7,500 files "change").
- SEO additions: `llms.txt` (tools/llms_txt.py), IndexNow (`python tools/indexnow.py` after deploy), price facts in area/sale FAQ
  (tools/thai/facts.py), outreach texts in tools/marketing/listing-kit.md. Bing Webmaster: Microsoft blocked account creation — retry later.
