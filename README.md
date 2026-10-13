# hCaptcha Solver API

**Self-hosted captcha-solving API** — same role as 2Captcha/CapSolver/Anti-Captcha for **hCaptcha**: your scraper, bot, or test runner sends **sitekey + page URL**, gets back a **`hCaptchaResponse` token** (~120s, single-use), and submits it to the target site.

Built for:

- Web scraping & data extraction when sessions hit hCaptcha  
- High-friction flows (Discord, Cloudflare-gated pages, signup walls)  
- Automated E2E / CI (no manual image clicks)  
- Optional **enterprise `rqdata`** and **proxy** per request  

Full integration flow: **[docs/INTEGRATION.md](docs/INTEGRATION.md)**  
Python client example: **[examples/automation_client.py](examples/automation_client.py)**

---

## Requirements

- Python 3.10+, Node.js 18+  
- NoCaptchaAI credentials (image challenges) in `.env`  
- Puppeteer Chromium (installed via `npm install` in `solver/`)

---

## Quick start

```bash
python3 scripts/setup.py
cp .env.example .env   # if needed
# Set API_AUTH_TOKEN, NOCAPTCHA_UID, NOCAPTCHA_APIKEY

python3 scripts/start.py
python3 scripts/smoke_test.py
```

---

## Solve a captcha

**JSON (automation / scrapers):**

```bash
curl -X POST "http://127.0.0.1:8080/api/v1/hcaptcha/solve" \
  -H "Authorization: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "site_key": "YOUR_SITEKEY",
    "site_url": "https://example.com/path",
    "rqdata": "optional",
    "proxy": "http://user:pass@host:8080"
  }'
```

**Response:**

```json
{
  "success": true,
  "hCaptchaResponse": "P0_eyJ...",
  "expires_in_seconds": 120,
  "solve_time": 12.4
}
```

Use `hCaptchaResponse` as **`h-captcha-response`** in your POST to the target site.

**2Captcha-compatible:**

```bash
curl "http://127.0.0.1:8080/in.php?key=YOUR_API_KEY&method=hcaptcha&sitekey=...&pageurl=..."
# => OK|P0_eyJ...
```

**Auth:** `Authorization` header, `X-API-Key`, or query `key` / `clientKey` (same value as `API_AUTH_TOKEN`).

Parameter aliases: `sitekey`, `pageurl`, `url`.

---

## Docker

```bash
cp .env.example .env
docker compose up --build
```

---

## Architecture

| Piece | Role |
|-------|------|
| `app.py` | Solver HTTP API |
| `solver/hsolver` | hCaptcha protocol (proofs, motion, submit) |
| `solver/browser.js` | hsw proof worker (:2030) |
| NoCaptchaAI | Remote image classification |

---

## License

See [LICENSE](LICENSE).
