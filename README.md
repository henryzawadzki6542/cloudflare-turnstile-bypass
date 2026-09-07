<a href="https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=cloudflare-turnstile-bypass">
  <img src="./assets/peak-banner.png" alt="Peak - solve Cloudflare Turnstile & the 5s challenge in ~1s" width="100%">
</a>

# Cloudflare Turnstile Bypass - How to Bypass the Turnstile Challenge in Python

**Cloudflare Turnstile Bypass** is a small, dependency-free Python package that
bypasses the Cloudflare Turnstile challenge programmatically: it **finds the
Turnstile sitekey** on any page, **creates a valid `cf-turnstile-response`
token** via the Peak API, and hands you the finished token - no browser, no
headless Chrome, no fingerprint fight. Designed for CI pipelines, QA
automation, and integration engineering.

**Table of Contents:**
- What "bypassing Turnstile" actually means
- Quick start
- Finding a Turnstile sitekey
- Bypassing the challenge
- Python API reference
- CLI usage
- Examples
- Why a solver beats headless browsers
- Powered by Peak
- License

## What "bypassing Turnstile" actually means

Cloudflare Turnstile is a challenge widget that issues a signed token. A
"bypass" never attacks Cloudflare's edge - that is not practical or legal. What
works, and what this package does, is:

1. **find the sitekey** the target page is protecting itself with,
2. **solve the challenge** for that sitekey through a solving service, and
3. **inject the resulting token** into your request exactly like a browser
   would after completing the widget.

To Cloudflare's backend your request now carries a valid, signed,
non-expired `cf-turnstile-response` - which is the entire contract the widget
enforces. That is the bypass.

## Quick start

```console
$ export PEAK_API_KEY=pk_your_api_key
$ python -m cloudflare_turnstile_bypass --url https://example.com/
0.AgAAABBqzz...
```

Or find the sitekey first, then bypass:

```python
from cloudflare_turnstile_bypass import find_sitekey, bypass_turnstile

sitekey = find_sitekey("https://example.com/")
token = bypass_turnstile("pk_...", sitekey, "https://example.com/")
print(token)  # -> "0.AgAAABBqzz..."
```

## Finding a Turnstile sitekey

Turnstile widgets expose the sitekey in the markup:

```html
<div class="cf-turnstile" data-sitekey="0x4AAAAAAAxxxx"></div>
```

`find_sitekey()` reads it for you:

```python
from cloudflare_turnstile_bypass import find_sitekey

sitekey = find_sitekey("https://example.com/")
print(sitekey)  # -> "0x4AAAAAAAxxxx"
```

Invisible (enterprise) widgets render the same attribute; if a page builds the
widget from JavaScript instead, the regex also matches `sitekey=` and
`render=` in the bundle source.

## Bypassing the challenge

```python
from cloudflare_turnstile_bypass import bypass_turnstile

token = bypass_turnstile(
    "pk_your_api_key",          # your Peak key (free, no card)
    "0x4AAAAAAAxxxx",           # the sitekey you found
    "https://example.com/",     # the page URL the widget lives on
)
# token is a valid cf-turnstile-response value
```

With a proxy (the solve runs on residential infrastructure, so the token
matches your exit IP region):

```python
token = bypass_turnstile(
    "pk_your_api_key",
    "0x4AAAAAAAxxxx",
    "https://example.com/",
    proxy="http://user:pass@proxy:8080",
)
```

## Python API reference

| Function | Purpose |
|---|---|
| `read_page(url)` | Fetch a page's HTML (plain `urllib`, no dependencies). |
| `find_sitekey(url)` | Extract the Turnstile sitekey from a page or HTML string. |
| `find_action(html)` | Extract an optional `data-action` value. |
| `bypass_turnstile(api_key, sitekey, url)` | Solve the challenge and return a ready token. |
| `token_for_page(api_key, url)` | Find + bypass in a single call, returns `BypassResult`. |

`BypassResult` carries `.token`, `.sitekey`, and the raw solver response.

## CLI usage

```console
$ python -m cloudflare_turnstile_bypass --url https://example.com/login
0.AgAAABBqzz...

$ python -m cloudflare_turnstile_bypass --url https://example.com/login --proxy http://user:pass@proxy:8080
```

Exit code 0 + the token on stdout - pipe it straight into `curl` or your
E2E test harness.

## Examples

See [`examples/submit_bypass.py`](examples/submit_bypass.py) for an end-to-end
flow: find the sitekey, bypass the challenge, and POST the token with your
form payload.

## Why a solver beats headless browsers

- **No browser to detect.** Turnstile fingerprints the browser environment;
  headless Chrome and CDP automation are exactly what it looks for.
- **One dependency-free file.** No Playwright, no Selenium, no matching
  Chromium build on your CI runner.
- **Pay for success.** Failed solves cost nothing; a headless fleet burns
  compute whether it passes or not.

> This package uses [Peak](https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=cloudflare-turnstile-bypass) to solve Turnstile.
> - Solve Cloudflare Turnstile & the 5s challenge in about a second
> - Pay only for successful solves - from $0.8 / 1,000
> - **1,000 free solves to start - no card.** [Grab 1,000 free solves](https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=cloudflare-turnstile-bypass)
>
> [Get your free API key](https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=cloudflare-turnstile-bypass) · [Docs](https://peak.fo/docs/turnstile?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=cloudflare-turnstile-bypass) · [Pricing](https://peak.fo/pricing?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=cloudflare-turnstile-bypass)

## License

MIT - see [LICENSE](LICENSE).
