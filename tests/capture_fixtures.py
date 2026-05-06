"""Capture live AudD API responses to fixtures/raw/ for spec validation.

Usage:
    AUDD_TEST_TOKEN_STD=... AUDD_TEST_TOKEN_ENTERPRISE=... \\
        python tests/capture_fixtures.py [--scenario NAME]

By default captures all scenarios. Pass --scenario NAME to capture one.

Hard rule: enterprise endpoint calls always include limit=1 to control cost.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).parent.parent
RAW = ROOT / "fixtures" / "raw"
EXAMPLE_MP3 = "https://audd.tech/example.mp3"  # 12-second sample, valid for both endpoints
INVALID_TOKEN = "definitelynotvalid_aaa"


def save(name: str, payload: dict | str, *, headers: dict | None = None) -> None:
    """Write a JSON-serialized capture (with optional response headers) to RAW."""
    out = {
        "captured_with_token_kind": payload.pop("__kind__", "unknown") if isinstance(payload, dict) else "unknown",
        "response_headers": headers or {},
        "response_body": payload,
    }
    path = RAW / f"{name}.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=False) + "\n")
    print(f"  saved {path.relative_to(ROOT)}")


def capture(client: httpx.Client, name: str, method: str, url: str, *, data: dict, kind: str) -> None:
    print(f"[{name}] {method} {url}")
    r = client.request(method, url, data=data, timeout=120)
    try:
        body = r.json()
    except Exception:
        body = {"_raw_text": r.text}
    body["__kind__"] = kind
    save(name, body, headers=dict(r.headers))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", help="only capture this named scenario")
    args = parser.parse_args()

    tok_std = os.environ.get("AUDD_TEST_TOKEN_STD")
    tok_ent = os.environ.get("AUDD_TEST_TOKEN_ENTERPRISE")
    if not tok_std or not tok_ent:
        print("ERROR: AUDD_TEST_TOKEN_STD and AUDD_TEST_TOKEN_ENTERPRISE must be set", file=sys.stderr)
        return 2

    scenarios = {
        # name, method, url, data, kind
        "recognize_basic": ("POST", "https://api.audd.io/", {
            "url": EXAMPLE_MP3, "api_token": tok_std,
        }, "standard_token"),
        "recognize_with_metadata": ("POST", "https://api.audd.io/", {
            "url": EXAMPLE_MP3,
            "return": "apple_music,spotify,deezer,napster,musicbrainz",
            "api_token": tok_std,
        }, "standard_token"),
        "error_900_invalid_token": ("POST", "https://api.audd.io/", {
            "url": EXAMPLE_MP3, "api_token": INVALID_TOKEN,
        }, "invalid_token"),
        "error_700_no_file": ("POST", "https://api.audd.io/", {
            "api_token": tok_std,
        }, "standard_token"),
        "error_19_no_callback_url": ("POST", "https://api.audd.io/getCallbackUrl/", {
            "api_token": tok_std,
        }, "standard_token"),
        "error_902_stream_limit": ("POST", "https://api.audd.io/addStream/", {
            "url": "https://npr-ice.streamguys1.com/live.mp3",
            "radio_id": "999001", "api_token": tok_std,
        }, "standard_token"),
        "error_904_enterprise_unauthorized": ("POST", "https://enterprise.audd.io/", {
            "url": EXAMPLE_MP3, "limit": "1", "api_token": tok_std,  # standard token, denied
        }, "standard_token"),
        "enterprise_with_isrc_upc": ("POST", "https://enterprise.audd.io/", {
            "url": EXAMPLE_MP3, "limit": "1", "api_token": tok_ent,  # enterprise success
        }, "enterprise_token"),
        "getStreams_empty": ("POST", "https://api.audd.io/getStreams/", {
            "api_token": tok_std,
        }, "standard_token"),
    }

    # Longpoll captures use a derived category; require GET, not POST.
    def cap_longpoll(client: httpx.Client) -> None:
        m1 = hashlib.md5(tok_std.encode()).hexdigest()
        m2 = hashlib.md5((m1 + "1").encode()).hexdigest()
        cat = m2[:9]
        url = f"https://api.audd.io/longpoll/?category={cat}&timeout=2"
        print(f"[longpoll_no_events] GET {url}")
        r = client.get(url, timeout=10)
        body = r.json()
        body["__kind__"] = "standard_token"
        save("longpoll_no_events", body, headers=dict(r.headers))

    client = httpx.Client(headers={"User-Agent": "audd-openapi-capture/0.1"})
    try:
        if args.scenario:
            if args.scenario == "longpoll_no_events":
                cap_longpoll(client)
            elif args.scenario in scenarios:
                method, url, data, kind = scenarios[args.scenario]
                capture(client, args.scenario, method, url, data=data, kind=kind)
            else:
                print(f"ERROR: unknown scenario {args.scenario}", file=sys.stderr)
                return 2
        else:
            for name, (method, url, data, kind) in scenarios.items():
                capture(client, name, method, url, data=data, kind=kind)
            cap_longpoll(client)
    finally:
        client.close()

    print("\nDone. Raw fixtures in fixtures/raw/.")
    print("Run Task 3 to scrub and curate them into fixtures/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
