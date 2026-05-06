# Fixtures

Real captured AudD API responses, used as the source of truth for SDK contract tests in every `audd-<lang>` repo.

| File | Source | Endpoint | Notes |
|---|---|---|---|
| `recognize_basic.json` | live capture | `POST api.audd.io/` | Standard recognition without metadata |
| `recognize_with_metadata.json` | live capture | `POST api.audd.io/` | Standard recognition with `return=apple_music,spotify,deezer,napster,musicbrainz` |
| `recognize_custom_match.json` | synthesized from design spec | `POST api.audd.io/` | Custom-catalog match shape (only `timecode` + `audio_id`) — can't easily capture live without enterprise custom-catalog access |
| `enterprise_with_isrc_upc.json` | live capture (enterprise token, `limit=1`) | `POST enterprise.audd.io/` | Enterprise success with ISRC and UPC fields |
| `error_900_invalid_token.json` | live capture | `POST api.audd.io/` | Invalid api_token |
| `error_700_no_file.json` | live capture | `POST api.audd.io/` | No file or url sent |
| `error_19_no_callback_url.json` | live capture | `POST api.audd.io/getCallbackUrl/` | The "no callback URL configured" signal — server returns code 19 (catch-all "Internal error") |
| `error_902_stream_limit.json` | live capture | `POST api.audd.io/addStream/` | Stream slots exhausted on subscription |
| `error_904_enterprise_unauthorized.json` | live capture | `POST enterprise.audd.io/` | Standard token denied at enterprise endpoint |
| `getStreams_empty.json` | live capture | `POST api.audd.io/getStreams/` | Empty stream list |
| `longpoll_no_events.json` | live capture | `GET api.audd.io/longpoll/` | Longpoll timeout response (no new events) |
| `streams_callback_with_result.json` | from docs.audd.io/streams.md | callback POSTed by AudD to user webhook | Recognition-result variant of the callback payload |
| `streams_callback_with_notification.json` | from docs.audd.io/streams.md | callback POSTed by AudD to user webhook | Notification variant (stream connectivity) |

Synthesized fixtures match the documented response shapes 1:1; they're called out explicitly so reviewers know which were captured live.

To re-capture: see `tests/capture_fixtures.py`. **Always pass `limit=1` for enterprise endpoint calls.**
