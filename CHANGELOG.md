# Changelog

All notable changes to this project are documented here.

## 1.0.1

- Fix `token_for_page` to forward `api_url`, `timeout` and `retries`; the CLI
  discovery path (without `--sitekey`) no longer errors and now honours
  `--api-url` and `--retries`.
- Move the `create_token` alias next to `bypass_turnstile`.
- Add unit tests and this changelog.

## 1.0.0

- First release: sitekey discovery, Peak token creation, CLI and example.
