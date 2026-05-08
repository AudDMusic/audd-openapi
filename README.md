# audd-openapi

[![CI](https://github.com/AudDMusic/audd-openapi/actions/workflows/ci.yml/badge.svg)](https://github.com/AudDMusic/audd-openapi/actions/workflows/ci.yml)

The canonical OpenAPI 3.1 specification for the [AudD](https://audd.io) music recognition API.

This repository is the source of truth that all official AudD SDKs build their typed models against. Third parties can also use this spec to generate their own clients.

| File | Purpose |
|---|---|
| [`openapi.yaml`](./openapi.yaml) | OpenAPI 3.1 spec covering every public AudD endpoint |
| [`fixtures/`](./fixtures/) | Real captured API responses, PII scrubbed — used by every SDK's contract tests |
| [`tests/validate.py`](./tests/validate.py) | Validates each fixture against its schema in `openapi.yaml` |
| [`tests/capture_fixtures.py`](./tests/capture_fixtures.py) | Re-capture fixtures from the live API (requires an api_token) |

## What's covered

- **Standard recognition** — `POST/GET https://api.audd.io/`
- **Enterprise recognition** — `POST https://enterprise.audd.io/` (hours- to days-long files)
- **Stream management** — `setCallbackUrl`, `getCallbackUrl`, `addStream`, `getStreams`, `setStreamUrl`, `deleteStream`
- **Longpoll** — `GET /longpoll/`
- **Custom catalog upload** — `POST /upload/` (special access required)
- **Lyrics search** — `POST /findLyrics/`

The WebSocket recognition variant is intentionally not modeled — AudD recommends the HTTP endpoints for all use cases.

## Validate locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python tests/validate.py
```

To re-capture fixtures from the live API:

```bash
AUDD_TEST_TOKEN_STD=... AUDD_TEST_TOKEN_ENTERPRISE=... \
    python tests/capture_fixtures.py
python tests/scrub_fixtures.py
```

## Generate a client

This spec is hand-written and validates against real fixtures. You can use it with any OpenAPI-compatible code generator. Note that AudD's official SDKs are hand-written rather than generated — to maximize idiomatic feel in each language — but they validate against this same spec.

## Contract drift detection

When this repo lands a change to `openapi.yaml` or `fixtures/`, a workflow fires `repository_dispatch` events at the nine SDK repos that have a separate contract workflow (audd-python, audd-node, audd-go, audd-rust, audd-php, audd-swift, audd-kotlin, audd-dotnet, audd-java) to re-run their contract tests against the new spec. Those nine SDKs also run the same contract tests on a daily cron at 06:00 UTC as a safety net. The audd-c and audd-cpp SDKs validate their parsers against fixtures inside their main CI build instead.

## License

MIT — see [LICENSE](./LICENSE).

## Support

- Documentation: https://docs.audd.io
- Tokens: https://dashboard.audd.io
- Email: api@audd.io
