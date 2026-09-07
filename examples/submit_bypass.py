"""Example: find a sitekey, create a token, and submit it."""

import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cloudflare_turnstile_bypass import token_for_page  # noqa: E402

API_KEY = os.environ.get("PEAK_API_KEY", "pk_your_api_key")
TARGET = "https://example.com/"


def main():
    result = token_for_page(API_KEY, TARGET)
    print("sitekey:", result.sitekey)
    print("token:", result.token[:24], "...")

    resp = requests.post(
        "https://example.com/submit",
        data={"cf-turnstile-response": result.token, "payload": "hello"},
        timeout=30,
    )
    print("submit status:", resp.status_code)


if __name__ == "__main__":
    main()