---
title: "Evidence bundle verifier (tamper-evident)"
status: done
version: "1.0.0"
last_updated: "2026-07-25"
claim_boundary: "Tamper-evidence within the bundle, no signature. Fixture packs prove Shared-gate honesty only. Checkpoint stays NO_GO."
---

# Wave I — Evidence bundle verifier (2026-07-25)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Separation of duties | SLSA provenance practice — producer writes digests, an **independent verifier** recomputes them; declared hashes are never trusted |
| Attestation protocols | arXiv 2605.21089 — evidence-driven verification of artifact authenticity/integrity |
| Internal regression class | RTATOM-G04 — dual-truth HTML (ambient PASSED vs enforced FAIL) must be structurally impossible to smuggle |

## Gap closed

`export_evidence_bundle` wrote `output_file_sha256` into the manifest, but
nothing ever **verified** a received/committed bundle: edited `findings.json`,
a flipped `PASSED` in `report.html`, or manifest count drift would go
unnoticed. The committed demo bundle (`artifacts/evidence-bundle/techlab-demo`)
was produced by a pre-hash exporter and had **no digests at all** — the new
verifier caught this immediately (honest FAIL), and the bundle was regenerated.

## Delivered (code + test + evidence)

- `tools/verify_evidence_bundle.py` — fail-closed verifier:
  - recomputes SHA-256 for every `output_file_sha256` entry; digest entries for
    absent files and declared artifacts without digests are findings;
  - dual-truth cross-checks: `report.json summary.passed` ↔
    `manifest.summary_passed_ambient`; `issue_count` ↔ report and
    `findings.json` length; `report.html` Shared-gate line ↔
    `manifest.summary_passed`; `reproducibility_hash` ↔ `run_manifest.json`;
  - exit 1 + explicit error list on any finding; missing manifest fails closed.
- `tests/test_verify_evidence_bundle.py` — 6 tests: fresh bundle passes;
  tampered findings / flipped HTML PASS / deleted artifact / manifest
  issue_count drift / missing manifest each fail (single export per class run).
- Regenerated `artifacts/evidence-bundle/techlab-demo` with the current
  exporter — now verifies: `verification="passed"`, `hashes_checked=8`.

## Explicitly NOT claimed

- No cryptographic signing / identity binding (hashes bind content only);
  future analog of SLSA L3 would add operator signatures.
- Bundle PASS remains fixture-class evidence — RT-001/002/003 unchanged.

## Gate evidence (2026-07-25 local)

`ruff format/check` PASS · `mypy src` 193 files PASS · `pytest tests -q`
**976 passed, 7 skipped** · committed demo bundle verifies (exit 0).
