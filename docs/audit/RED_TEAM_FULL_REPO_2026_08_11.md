"""Red Team full-repo pass — 2026-08-11 (Windows + VLM contour).

## Scope

Full ``pytest`` after mentor/VLM Red Team. Failures + P1 contour gaps closed.

## P0 — Review-event filesystem (Windows)

| Finding | Evidence | Fix |
|---|---|---|
| ``pack:{id}`` report paths become NTFS Alternate Data Streams | ``Path('pack:x.jsonl')`` creates file ``pack`` + ADS; ``iterdir`` misses seq/lock → second append ``Could not acquire review-event lock`` | ``FilesystemReviewEventStore._path`` uses ``safe_storage_token`` |
| Shared journal across tenants | ``report_id=f"pack:{pack_id}"`` ignored tenant | ``ApplyNormRuleHitlEventUseCase`` → ``pack:{tenant}:{pack_id}`` |

## P1 — Yandex + default kimi-k3

Mentor already refused; DI ``vlm_advisory_ready`` / region+advisory smokes still allowed wrong profile.

Shared gate: ``aerobim.core.config.vlm_endpoint_gate.refuse_yandex_kimi_default_model``.

## Golden hash

Conscious refresh ``aa641ac5…`` → ``62ade6f0…`` after MEP-CLASH-001 honesty probe / engine signature drift since Aug 3 baseline pin. Status+engine only (reasons not hashed).

## Not fixed (by design / tracked)

- Checkpoint RT-001/002/003 NO_GO
- ODA / MEP ``@sota-stub`` (KNOWN_BUGS)
- OIDC BFF honesty 501 stubs
