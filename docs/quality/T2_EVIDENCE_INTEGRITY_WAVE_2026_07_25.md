---
title: "T2 evidence integrity: hash recomputation + T1 artifact binding"
status: done
version: "1.0.0"
last_updated: "2026-07-25"
claim_boundary: "Hardens the T2 gate only. T2 itself stays NOT_VERIFIED until a real customer CDE import pack lands (RT-008). Checkpoint stays NO_GO."
---

# Wave H — T2 evidence integrity (2026-07-25)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Artifact binding | SLSA provenance practice — evidence must bind to the verified digest of the actual artifact (slsa.dev; 2026 guides) |
| Evidence-driven attestations | arXiv 2605.21089 — evidence protocol for trustworthy pipelines: verify authenticity/integrity/provenance, never trust declared hashes |
| Consumer reality | BIMcollab BCF 3.0 import (2026-02-20); Trimble Connect BCF 2.1 — runbook targets |

## Integrity gap closed

`verify_bcf_t2_evidence` previously accepted **any non-empty** `hashes.json`:
a stale or foreign hash pack (proof of importing a *different* BCF) could flip
`claim_allowed` once STATUS said VERIFIED. Recomputation and binding were
design intent (template has `bcf_zip_sha256`; README says "SHA-256 of BCF ZIP
+ screenshot + log") but never enforced.

## Delivered (code + test + docs)

- `tools/verify_bcf_t2_evidence.py` (schema 1.1.0):
  - every `hashes.json` entry naming a pack file is **recomputed** (SHA-256,
    streamed) and must match; entries for absent files are mismatches;
  - `import-log.txt` / `screenshot.png` must each have a verified entry —
    present-but-unbound files block the claim;
  - `--structural-evidence <T1 json>`: declared `bcf_zip_sha256` (or
    `*.bcf`/`*.bcfzip` key) must equal a `bcf_21`/`bcf_30` `sha256` from the
    T1 structural handoff — the import proof provably refers to the archive we
    exported; mismatch reason: "import proof refers to a different archive";
  - new payload fields: `hashes_verified`, `hash_mismatches`, `bcf_binding`;
    fail-closed reasons; backward compatible when binding is not requested.
- `tests/test_bcf_t2_hash_binding.py` — 8 tests: valid pack passes; tampered
  hash / absent-file entry / unbound required file each block; binding match,
  foreign digest, missing digest, no-binding compatibility.
- `audit/evidence/cde-import-proof/README.md` — integrity-gate section.
- `docs/pilot/BCF_T2_IMPORT_RUNBOOK_2026.md` — step-by-step pilot protocol
  (T1 refresh → export → CDE import → pack capture → fail-closed verification
  → wording discipline).

## Explicitly NOT claimed

- T2 remains **NOT_VERIFIED** — the repo pack is still the empty template; no
  screenshots/logs are invented (RT-008 unchanged).
- No cryptographic signing of packs (future: operator signature per SLSA L3
  analog) — hashes bind content, not identity.

## Gate evidence (2026-07-25 local)

`ruff format/check` PASS · `mypy src` 192 files PASS · `pytest tests -q`
**970 passed, 7 skipped** (incl. legacy honesty tests unchanged).
