<!-- claims-lint: allow-file reason="VLM fixture statuses; comparison_not_run; not a bake-off" -->
# VLM stamp comparison (tracker 2.2)

**status:** `LIVE`
**comparison_status:** `comparison_not_run`
**qwen_fixture_status:** `LIVE`
**kimi_status:** `GATED`
**claim_level:** `fixture_only`

VLM advisory on open fixture title-block/spec crops. Stamp pixels are not sent (PII clip). fixture_only. Not door/window counting. Not product accuracy. Invalid JSON → fail-closed skip for that region.

Qwen is LIVE on this open fixture (structured roundtrip recorded 2026-08-13). Kimi is GATED on the Studio host. comparison_status=comparison_not_run: same input/prompt/schema was not executed for both models. Not a bake-off. Not product accuracy. Does not close RT-001.

| Model | Status | elapsed_ms | regions_read | observations | schema_fail_share |
|---|---|---:|---:|---:|---:|
| Qwen | roundtrip_ok | 1606.1 | 1 | 1 | 0.0 |
| Kimi | GATE_REFUSED | — | — | — | — |

content_sha256: `969da6d9f9f709840d87a5de7e6b8d5b9d6719241250db12b6f3cd6dba3f4101`
generated_at: `2026-08-13T20:21:47.237117+00:00`
