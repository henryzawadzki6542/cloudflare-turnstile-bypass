"""Example: bypass several protected pages in one run.

Each token is bound to the page URL it was solved for, so solve the exact
page you are about to submit to - never reuse a token across pages.

Usage:
    python examples/batch_pages.py https://example.com/login https://example.com/checkout
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cloudflare_turnstile_bypass import token_for_page  # noqa: E402

API_KEY = os.environ.get("PEAK_API_KEY", "")
PAGES = [
    "https://example.com/login",
    "https://example.com/checkout",
]


def main(pages):
    for url in pages:
        result = token_for_page(API_KEY, url)
        print(f"{url} -> {result.token[:28]}...")


if __name__ == "__main__":
    main(sys.argv[1:] or PAGES)
