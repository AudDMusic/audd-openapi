"""Promote fixtures from fixtures/raw/ to fixtures/, stripping captured-with
metadata and verifying no api_token leaked through.

Reads AUDD_TEST_TOKEN_STD and AUDD_TEST_TOKEN_ENTERPRISE from the env (same as
capture_fixtures.py) and checks that neither appears unredacted in any fixture
body. If env vars are absent, falls back to a heuristic 32-hex scan (which can
false-positive on Spotify/MusicBrainz IDs and similar — preferred to use the
exact-token check).

Usage: python tests/scrub_fixtures.py
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
RAW = ROOT / "fixtures" / "raw"
OUT = ROOT / "fixtures"

HEX32_RE = re.compile(r"\b[0-9a-f]{32}\b")
ALLOW_REDACTED = re.compile(r"^.\*+.$")


def scan_for_leaks(blob: str, exact_tokens: list[str]) -> list[str]:
    """Return any leaked token-shaped strings.

    If `exact_tokens` is non-empty, only flag substrings that match one of the
    provided tokens (precise mode). Otherwise fall back to "any 32-hex string"
    (imprecise — used only when tokens aren't in env).
    """
    if exact_tokens:
        return [t for t in exact_tokens if t in blob]
    findings = []
    for m in HEX32_RE.findall(blob):
        if not ALLOW_REDACTED.match(m):
            findings.append(m)
    return findings


def main() -> int:
    if not RAW.exists():
        print("No fixtures/raw/ directory; run capture_fixtures.py first.", file=sys.stderr)
        return 2

    exact = [t for t in (
        os.environ.get("AUDD_TEST_TOKEN_STD"),
        os.environ.get("AUDD_TEST_TOKEN_ENTERPRISE"),
    ) if t]
    if exact:
        print(f"  using exact-token check (got {len(exact)} token(s) from env)")
    else:
        print("  WARN: tokens not in env; falling back to imprecise 32-hex scan")

    failures: list[str] = []
    for path in sorted(RAW.glob("*.json")):
        outer = json.loads(path.read_text())
        body = outer["response_body"]
        body.pop("__kind__", None)
        text = json.dumps(body)

        leaks = scan_for_leaks(text, exact)
        if leaks:
            failures.append(f"{path.name}: token leaked through: {leaks}")
            continue

        out_path = OUT / path.name
        out_path.write_text(json.dumps(body, indent=2, sort_keys=False) + "\n")
        print(f"  curated {out_path.relative_to(ROOT)}")

    if failures:
        print("\nABORT: scrub failed:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("\nAll fixtures curated. Inspect them before committing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
