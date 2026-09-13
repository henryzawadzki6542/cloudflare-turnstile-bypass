"""Unit tests for cloudflare_turnstile_bypass - standard library only."""

import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cloudflare_turnstile_bypass as mod  # noqa: E402

HTML = '<div class="cf-turnstile" data-sitekey="0xAAA" data-action="login"></div>'


class FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestDiscovery(unittest.TestCase):
    def test_find_sitekey_from_html(self):
        self.assertEqual(mod.find_sitekey("https://example.com/", HTML), "0xAAA")

    def test_find_sitekey_missing_raises(self):
        with self.assertRaises(mod.TurnstileBypassError):
            mod.find_sitekey("https://example.com/", "<html>nothing</html>")

    def test_find_action(self):
        self.assertEqual(mod.find_action(HTML), "login")
        self.assertIsNone(mod.find_action("<html>nothing</html>"))


class TestPayload(unittest.TestCase):
    def test_minimal(self):
        p = mod.build_payload("0xAAA", "https://example.com/")
        self.assertEqual(p["task_type"], "turnstiletask")
        self.assertNotIn("proxy", p)

    def test_optionals(self):
        p = mod.build_payload("0xAAA", "https://example.com/",
                              proxy="http://u:p@1.2.3.4:8080", action="login", cdata="c")
        self.assertEqual(p["proxy"], "http://u:p@1.2.3.4:8080")
        self.assertEqual(p["action"], "login")
        self.assertEqual(p["cdata"], "c")


class TestBypass(unittest.TestCase):
    def test_missing_key_raises(self):
        with self.assertRaises(mod.TurnstileBypassError):
            mod.bypass_turnstile("", "0xAAA", "https://example.com/")

    def test_success(self):
        payload = {"success": True, "data": {"token": "0.TOK"}}
        with mock.patch.object(mod, "urlopen", return_value=FakeResponse(payload)):
            res = mod.bypass_turnstile("pk_x", "0xAAA", "https://example.com/")
        self.assertEqual(res.token, "0.TOK")
        self.assertEqual(res.sitekey, "0xAAA")

    def test_api_error(self):
        payload = {"success": False, "error": "bad sitekey"}
        with mock.patch.object(mod, "urlopen", return_value=FakeResponse(payload)):
            with self.assertRaises(mod.TurnstileBypassError):
                mod.bypass_turnstile("pk_x", "0xAAA", "https://example.com/")

    def test_token_for_page_forwards_api_url(self):
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            return FakeResponse({"success": True, "data": {"token": "0.Y"}})

        with mock.patch.object(mod, "urlopen", side_effect=fake_urlopen):
            mod.token_for_page("pk_x", "https://example.com/", html=HTML,
                               api_url="https://api.test/solve")
        self.assertEqual(captured["url"], "https://api.test/solve")


class TestCli(unittest.TestCase):
    def test_version(self):
        with self.assertRaises(SystemExit) as ctx:
            mod.main(["--url", "https://example.com/", "--version"])
        self.assertEqual(ctx.exception.code, 0)

    def test_discovery_path_works(self):
        # regression: main() used to pass api_url to token_for_page, which
        # did not accept it -> TypeError on the default (no --sitekey) path.
        payload = {"success": True, "data": {"token": "0.Z"}}
        with mock.patch.object(mod, "read_page", return_value=HTML), \
                mock.patch.object(mod, "urlopen", return_value=FakeResponse(payload)):
            rc = mod.main(["--url", "https://example.com/", "--api-key", "pk_x"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
