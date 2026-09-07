"""cloudflare-turnstile-bypass: bypass the Cloudflare Turnstile challenge in Python.

A small, dependency-free Python package that:

- **finds** the Turnstile sitekey on any page (widget discovery),
- **creates** a valid ``cf-turnstile-response`` token via the Peak API,
- and ships a CLI you can pipe into CI and shell scripts.

Typical use::

    from cloudflare_turnstile_bypass import find_sitekey, create_token

    sitekey = find_sitekey("https://example.com/")
    token = create_token("pk_...", sitekey, "https://example.com/")
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Optional
from urllib.request import Request, urlopen

__version__ = "1.0.0"

DEFAULT_API_URL = "https://api.peak.fo/solve"
ENV_API_KEY = "PEAK_API_KEY"

_SITEKEY_RE = re.compile(
    r"""data-sitekey\s*=\s*["']([^"']+)["']"""
    r"""|(?:sitekey|render)\s*[:=]\s*["']([^"']+)["']""",
    re.I,
)
_ACTION_RE = re.compile(r"""data-action\s*=\s*["']([^"']+)["']""", re.I)


class TurnstileBypassError(RuntimeError):
    """Raised when a sitekey cannot be found or a token cannot be created."""


@dataclass
class BypassResult:
    token: str
    sitekey: str
    raw: dict


def read_page(url: str, timeout: float = 30.0) -> str:
    """Fetch a page and return its text body."""
    req = Request(url, headers={"User-Agent": "cloudflare-turnstile-bypass/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def find_sitekey(url: str, html: Optional[str] = None) -> str:
    """Find the Turnstile sitekey on a page (fetching it if html is not given)."""
    if html is None:
        html = read_page(url)
    for match in _SITEKEY_RE.finditer(html):
        candidate = next((g for g in match.groups() if g), None)
        if candidate:
            return candidate.strip()
    raise TurnstileBypassError("no Turnstile sitekey found on the page")


def find_action(html: str) -> Optional[str]:
    """Find an optional Turnstile data-action value on the page."""
    m = _ACTION_RE.search(html or "")
    return m.group(1).strip() if m else None


def build_payload(
    sitekey: str,
    url: str,
    proxy: Optional[str] = None,
    action: Optional[str] = None,
    cdata: Optional[str] = None,
) -> dict:
    """Build the Peak solve payload for a Turnstile token."""
    payload = {"task_type": "turnstiletask", "sitekey": sitekey, "url": url}
    if proxy:
        payload["proxy"] = proxy
    if action:
        payload["action"] = action
    if cdata:
        payload["cdata"] = cdata
    return payload


def bypass_turnstile(
    api_key: str,
    sitekey: str,
    url: str,
    proxy: Optional[str] = None,
    action: Optional[str] = None,
    cdata: Optional[str] = None,
    api_url: str = DEFAULT_API_URL,
    timeout: float = 180.0,
    retries: int = 3,
) -> BypassResult:
    """Create a valid Turnstile token via the Peak API.

    Raises :class:`TurnstileBypassError` on failure.
    """
    if not api_key:
        raise TurnstileBypassError(
            "No API key. Set PEAK_API_KEY or pass an api_key "
            "(get 1,000 free solves to start - no card - at https://peak.fo)."
        )
    payload = build_payload(sitekey, url, proxy, action, cdata)
    body = json.dumps(payload).encode("utf-8")
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        req = Request(api_url, data=body, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            last_err = exc
            if attempt < retries:
                time.sleep(2 * attempt)
                continue
            raise TurnstileBypassError(
                f"Peak request failed after {retries} attempts: {exc}"
            ) from exc
        if not data.get("success"):
            raise TurnstileBypassError(data.get("error") or "Peak solve failed")
        token = (data.get("data") or {}).get("token")
        if not token:
            raise TurnstileBypassError("Peak response missing data.token")
        return BypassResult(token=token, sitekey=sitekey, raw=data)
    raise TurnstileBypassError(f"Peak request failed: {last_err}")


def token_for_page(
    api_key: str,
    url: str,
    proxy: Optional[str] = None,
    html: Optional[str] = None,
) -> BypassResult:
    """One call: find the sitekey on a page, then create a token for it."""
    if html is None:
        html = read_page(url)
    sitekey = find_sitekey(url, html)
    action = find_action(html)
    return create_token(api_key, sitekey, url, proxy=proxy, action=action)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cloudflare-turnstile-bypass",
        description="Find a Turnstile sitekey and create a valid token via the Peak API.",
    )
    parser.add_argument("--url", required=True, help="Target page URL (ending with '/')")
    parser.add_argument("--sitekey", help="Skip discovery and use this sitekey directly")
    parser.add_argument("--proxy", help="Proxy in http://user:pass@ip:port format")
    parser.add_argument("--api-key", default=os.environ.get(ENV_API_KEY, ""))
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    try:
        if args.sitekey:
            result = create_token(args.api_key, args.sitekey, args.url,
                                  proxy=args.proxy, api_url=args.api_url,
                                  retries=args.retries)
        else:
            result = token_for_page(args.api_key, args.url, proxy=args.proxy,
                                    api_url=None)
    except TurnstileBypassError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output == "json":
        print(json.dumps({"sitekey": result.sitekey, "token": result.token,
                          "success": True}, indent=2))
    else:
        print(result.token)
    return 0


if __name__ == "__main__":
    sys.exit(main())


# Alias: some callers prefer the neutral name.
create_token = bypass_turnstile
