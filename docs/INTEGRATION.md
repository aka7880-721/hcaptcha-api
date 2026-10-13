# hCaptcha solver API — integration guide

This service returns a **pass token** (`generated_pass_UUID` / `P0_ey...`) that you submit as **`h-captcha-response`** (or `hCaptchaResponse`) on the target site—the same value commercial solvers (2Captcha, CapSolver, etc.) provide.

## Token flow

```mermaid
sequenceDiagram
    participant Bot as Your automation
    participant Solver as This API
    participant HC as hcaptcha.com
    participant Site as Target website

    Bot->>Solver: sitekey + pageurl (+ rqdata, proxy)
    Solver->>HC: checksiteconfig / getcaptcha / proofs / checkcaptcha
    Solver-->>Bot: hCaptchaResponse token (~120s TTL, single-use)
    Bot->>Site: POST login/signup with h-captcha-response=token
    Site->>HC: siteverify (secret on server)
    HC-->>Site: success / fail
```

1. **Sitekey** — from `data-sitekey` or network tab on the protected page.  
2. **Page URL** — full URL of the page where the widget runs (affects host / motion).  
3. **Solve** — call this API; receive token.  
4. **Consume** — within ~120 seconds, send token once with your form/API request.  
5. **Verify** — the **target site** validates with hCaptcha using its **secret**; your bot only needs the token.

## API endpoints

### JSON (recommended)

```http
POST /api/v1/hcaptcha/solve
Authorization: YOUR_API_KEY
Content-Type: application/json

{
  "site_key": "f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34",
  "site_url": "https://discord.com/register",
  "rqdata": "optional-enterprise-payload",
  "proxy": "http://user:pass@host:8080"
}
```

**Success:**

```json
{
  "success": true,
  "status": "ready",
  "token": "P0_eyJ0...",
  "hCaptchaResponse": "P0_eyJ0...",
  "generated_pass_UUID": "P0_eyJ0...",
  "solve_time": 14.2,
  "expires_in_seconds": 120
}
```

### Query (simple scrapers)

```http
GET /solve?sitekey=...&pageurl=...&key=YOUR_API_KEY
Authorization: YOUR_API_KEY
```

### 2Captcha-style (plain text)

```http
GET /in.php?key=YOUR_API_KEY&method=hcaptcha&sitekey=...&pageurl=...
```

Response: `OK|P0_eyJ0...` or `ERROR|MESSAGE`

## Use cases

| Use case | Notes |
|----------|--------|
| **Scraping** | Solve when a session hits hCaptcha; reuse token once for that request. |
| **Bot / signup flows** | Discord, Epic, etc. often need **`rqdata`** from the page — pass it through. |
| **E2E / CI** | Point tests at this API instead of manual clicks. |
| **Proxies** | Pass `proxy` so egress IP matches your automation session. |

## Server-side verify (target site)

Your solver returns the **client token**. The **website owner** verifies:

```http
POST https://api.hcaptcha.com/siteverify
secret=SITE_SECRET&response=TOKEN
```

You do **not** need the site secret to use this solver—only the token for the protected action.

## Python example

See [`examples/automation_client.py`](../examples/automation_client.py).

## Operational notes

- Run **`python scripts/start.py`** (hsw + Flask). Image challenges need **NoCaptchaAI** keys in `.env`.  
- Scale with **multiple Gunicorn workers**; each solve is CPU/network heavy.  
- Tokens **cannot be reused**; request a fresh solve per blocked action.
