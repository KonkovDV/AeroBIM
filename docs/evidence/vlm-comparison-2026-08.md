# VLM stamp comparison (tracker 2.2)

**status:** `LIVE`
**claim_level:** `fixture_only`

VLM advisory on open fixture title-block/spec crops. Stamp pixels are not sent (PII clip). fixture_only. Not door/window counting. Not product accuracy. Invalid JSON → fail-closed skip for that region.

Take Qwen on Yandex AI Studio for this RF contour: live structured roundtrip on the open title-block/spec crops succeeded; Kimi-k3 is refused on the Studio host by design. This is not product accuracy and does not close RT-001. Stamp pixels stay off the wire (PII clip).

| Model | Status | elapsed_ms | regions_read | observations | schema_fail_share |
|---|---|---:|---:|---:|---:|
| Qwen | roundtrip_ok | 1606.1 | 1 | 1 | 0.0 |
| Kimi | GATE_REFUSED | — | — | — | — |

content_sha256: `b542a608242276d33f4ba06b272125dbfdee0e8f741169e2d8f18edfe6104f01`
generated_at: `2026-08-13T20:21:47.237117+00:00`
