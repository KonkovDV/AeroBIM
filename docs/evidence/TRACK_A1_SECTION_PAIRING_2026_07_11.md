---
title: "Track A1 — Section pairing hardening"
status: complete-engineering
delivered_at: "2026-07-11"
tags: [aerobim, p1, section-pairing, track-a]
---

# Track A1 — Section pairing hardening (2026-07-11)

Strengthens the deterministic PD↔RD section-pairing scaffold **without** any
customer corpus. Scope from the AeroBIM priority list Track A1: *"больше
дисциплин, capability status, canonical keys"*.

## What changed

| Item | Before P1 | After A1 |
|---|---|---|
| Disciplines | single AR string, `АР`≠`AR` false mismatch | canonical registry, 14 RU/EN marks, `АР`↔`AR` fold |
| Key matching | raw-string exact key | **canonical-key** registry (discipline-scoped + common), RU/EN aliases |
| Capability status | `paired a -> b; findings=N` | `paired <CODE> [recognized] a -> b; canonical-key coverage=k/n; findings=N` |
| Rule ids | `_slug` collapsed Cyrillic to `VALUE` | deterministic Cyrillic→Latin transliteration (`КЖ`→`KZH`) |
| Ambiguity | n/a | two keys → one canonical ⇒ **fail-closed** `ValueError` |
| Fixtures | AR only | + КЖ (Cyrillic stage/mark, RU alias `защитный.слой`→`rebar.cover`) |

## Atomic delivery (Clean Architecture preserved)

- **Domain** (`domain/section_pairing.py`, new): `DisciplineInfo`,
  `CanonicalKeyResult`, `SectionPairingReport`, `canonicalize_discipline`,
  `canonicalize_key`, `normalize_key`, `slugify`, `transliterate`. Imports only
  `domain.models` — no Application/Infrastructure imports.
- **Port** (`domain/ports.py`): `SectionDiffAnalyzer` gains
  `analyze(...) -> SectionPairingReport`; `compare(...)` retained (delegates).
- **Adapter** (`infrastructure/.../json_section_diff_analyzer.py`): canonical-key
  matching, canonical-discipline metadata compare, transliterated rule ids,
  canonical-collision fail-closed, `analyze()` builds coverage report.
- **Application** (`analyze_project_package.py`): `_collect_section_pairing_issues`
  now calls `analyze()` and emits the enriched capability `reason`.
- **DI**: existing `Tokens.SECTION_DIFF_ANALYZER` + bootstrap unchanged (default
  built-in registries; constructor stable).

## Verification

- Focused: `test_section_pairing_registry.py` (new, 11 tests),
  `test_section_diff_analyzer.py` (+6: coverage, KZH cross-language, Cyrillic
  rule ids, RU/EN discipline fold, ambiguity fail-closed, schema conformance),
  `test_p1_norm_section_integration.py` (+coverage assertion).
- Full backend: **364 passed, 2 skipped** (baseline 347/2; +17 new tests, 0
  regressions).
- Layer boundaries (`test_layer_boundaries.py`) and Wave-0 soundness green.
- No change to auth / path jail / multipart upload / capabilities honesty.

## Claim boundary (unchanged)

Delivered: harness + registries + scaffolds + capabilities honesty. The canonical
registry is a **scaffold vocabulary** seeded for synthetic residential data — it
is **not** a claim of full SP/GOST canonical-key coverage, and reports no customer
accuracy. Unknown disciplines/keys are compared but flagged `recognized=False`.

## Customer blockers still open

1. Real approved PD↔RD pair (AR or KZH) + frozen customer **canonical-key** list.
2. Adjudicated corpus before any publishable precision (`DETECTION_PRECISION_PROTOCOL_2026.md`).
3. Two adjudicators + baseline review hours.
