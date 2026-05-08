"""Validate every fixture in fixtures/ against its expected schema in openapi.yaml.

Mapping (fixture-name → schema-name) lives below as FIXTURE_SCHEMA. Add an entry
for each new fixture as Tasks 5-13 add their schemas.

Usage: python tests/validate.py
Exits non-zero on any validation failure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).parent.parent
SPEC = ROOT / "openapi.yaml"
FIXTURES = ROOT / "fixtures"

# Add a row here whenever a new fixture or schema lands.
FIXTURE_SCHEMA: dict[str, str] = {
    "recognize_basic.json": "RecognizeSuccessResponse",
    "recognize_with_metadata.json": "RecognizeSuccessResponse",
    "recognize_custom_match.json": "RecognizeSuccessResponse",
    "error_900_invalid_token.json": "ErrorResponse",
    "error_700_no_file.json": "ErrorResponse",
    "enterprise_with_isrc_upc.json": "EnterpriseSuccessResponse",
    "error_904_enterprise_unauthorized.json": "ErrorResponse",
    "error_19_no_callback_url.json": "ErrorResponse",
    "error_902_stream_limit.json": "ErrorResponse",
    "getStreams_empty.json": "GetStreamsSuccessResponse",
    "streams_callback_with_result.json": "StreamCallbackPayload",
    "streams_callback_with_notification.json": "StreamCallbackPayload",
    "longpoll_no_events.json": "LongpollResponse",
    # "error_19_no_callback_url.json": "ErrorResponse",
    # "error_902_stream_limit.json": "ErrorResponse",
    # "error_904_enterprise_unauthorized.json": "ErrorResponse",
    # "getStreams_empty.json": "GetStreamsSuccessResponse",
    # "longpoll_no_events.json": "LongpollResponse",
    # "streams_callback_with_result.json": "StreamCallbackPayload",
    # "streams_callback_with_notification.json": "StreamCallbackPayload",
}


SPEC_BASE_URI = "urn:audd-openapi"


def build_registry(spec: dict) -> Registry:
    """Register the full spec under a base URI so '#/components/schemas/Foo' refs resolve."""
    return Registry().with_resource(
        SPEC_BASE_URI,
        Resource(contents=spec, specification=DRAFT202012),
    )


def schema_with_id(component_schema: dict) -> dict:
    """Wrap a component schema with an $id pointing into the registered spec so its
    relative $ref pointers (#/components/schemas/X) resolve via the registry."""
    return {**component_schema, "$id": SPEC_BASE_URI}


def main() -> int:
    spec = yaml.safe_load(SPEC.read_text())
    schemas = spec["components"]["schemas"]
    registry = build_registry(spec)

    failures: list[str] = []
    skipped: list[str] = []
    for fixture_name, schema_name in FIXTURE_SCHEMA.items():
        fix_path = FIXTURES / fixture_name
        if not fix_path.exists():
            skipped.append(fixture_name)
            continue
        if schema_name not in schemas:
            failures.append(f"{fixture_name}: schema {schema_name} not in spec")
            continue
        # Resolve the schema by $ref so the registry-loaded spec is the resolution root.
        ref_schema = {"$ref": f"{SPEC_BASE_URI}#/components/schemas/{schema_name}"}
        validator = Draft202012Validator(ref_schema, registry=registry)
        errors = sorted(validator.iter_errors(json.loads(fix_path.read_text())),
                        key=lambda e: list(e.absolute_path))
        if errors:
            for e in errors:
                failures.append(f"{fixture_name}: {list(e.absolute_path)}: {e.message}")
        else:
            print(f"  ok {fixture_name} validates against {schema_name}")

    # Also flag fixtures that don't have a mapping.
    mapped = set(FIXTURE_SCHEMA.keys())
    on_disk = {p.name for p in FIXTURES.glob("*.json")}
    orphans = sorted(on_disk - mapped)
    if orphans:
        print(f"\n[!] unmapped fixtures (add to FIXTURE_SCHEMA): {orphans}")

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"\n{len(FIXTURE_SCHEMA) - len(skipped)} fixtures validated.")
    return 0 if not orphans else 1


if __name__ == "__main__":
    sys.exit(main())
