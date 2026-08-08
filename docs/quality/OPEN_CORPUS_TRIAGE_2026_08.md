<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "Open corpus triage — IFC schema suite + known gaps"
date: 2026-08-07
status: active
claim_boundary: >-
  Triage only. Checkpoint NO_GO. No product accuracy >90%.
  Document gaps honestly; do not greenwash honest non-support as parser bugs.
---

# Open corpus triage (2026-08)

**Purpose:** Triage the in-repo IFC schema regression suite and classify failures as **parser bug**, **rule gap**, or **honest non-support**.  
**Scope this week:** document only — no cheap (a)/(b) code fixes unless the suite proves a true parser bug.

Related: [`ifc-compatibility-matrix.md`](../ifc-compatibility-matrix.md), [`open-corpora/profiles/regression.json`](../../samples/benchmarks/open-corpora/profiles/regression.json), [`OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md`](OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md).

---

## Suite run (2026-08-07, fixture_only)

Evidence: [`docs/evidence/ifc-release-benchmark-2026-08.md`](../evidence/ifc-release-benchmark-2026-08.md).

| Schema | issue_count | Notes |
|---|---:|---|
| IFC2X3 | 6 | Higher than IFC4/4X3 — consistent with Qto vs BaseQuantities IDS facet (honest non-support / degradation), not a new parser bug |
| IFC4 | 4 | Baseline for this pack |
| IFC4X3 | 4 | Matches IFC4 pack shape on this fixture |

**Decision this week:** no cheap (a)/(b) code fix — classify IFC2x3 delta as **honest non-support** / known degradation, document only.

**Sprint 3 open-data intake:** no new third-party expertise packages vendored (no license-clear document↔remark corpus; budget $0 for paid SDKs). Existing buildingSMART / IFC-Bench / IDS testcases remain fixture/open-bench only — see [`docs/datasets/expertise-corpus-scan-2026-08.md`](../datasets/expertise-corpus-scan-2026-08.md).

---

## Fixture suite under triage

| Fixture | IFC release | IDS | Key expectations |
|---|---|---|---|
| [`wall-pset-qto-pass.ifc`](../../samples/ifc/wall-pset-qto-pass.ifc) | **IFC4** | [`wall-pset-qto.ids`](../../samples/ids/wall-pset-qto.ids) | `Pset_WallCommon.FireRating=REI60`; `Qto_WallBaseQuantities.Width` present |
| [`wall-pset-ifc2x3.ifc`](../../samples/ifc/wall-pset-ifc2x3.ifc) | **IFC2x3** | same IDS | `Pset_WallCommon.FireRating=REI60`; **`BaseQuantities.Width`** (not `Qto_*`) |
| [`wall-pset-ifc4x3.ifc`](../../samples/ifc/wall-pset-ifc4x3.ifc) | **IFC4x3** | same IDS | `Pset_WallCommon.FireRating=REI60`; `Qto_WallBaseQuantities.Width` present |
| [`wall-pset-qto-missing-qto.ifc`](../../samples/ifc/wall-pset-qto-missing-qto.ifc) | **IFC4** | same IDS | Pset OK; Qto absent — expect fail |

IDS declares `ifcVersion="IFC2X3 IFC4 IFC4X3_ADD2"` for both specifications (FireRating + Width quantity).

---

## Triage matrix

| # | Check | IFC4 pass fixture | IFC2x3 fixture | IFC4x3 fixture | Classification |
|---|---|---|---|---|---|
| T1 | IfcOpenShell opens file | ✅ | ✅ | ✅ | — |
| T2 | `Pset_WallCommon.FireRating=REI60` found | ✅ | ✅ | ✅ | — |
| T3 | IDS FireRating spec passes (IfcTester) | ✅ | ✅ | ✅ | — |
| T4 | Quantity set name in file | `Qto_WallBaseQuantities` | **`BaseQuantities`** | `Qto_WallBaseQuantities` | **Honest non-support (IFC2x3)** — schema naming divergence per [`ifc-compatibility-matrix.md`](../ifc-compatibility-matrix.md) |
| T5 | IDS asks for `Qto_WallBaseQuantities.Width` | Present → pass | **Name mismatch** — IDS facet targets `Qto_*`; file has `BaseQuantities.Width=0.3` | Present → pass | **Honest non-support (IFC2x3)** if engine reports missing Qto; **not** a product bug to greenwash. Degradation rule: fallback to `BaseQuantities` matching; emit INFO, not false ERROR |
| T6 | Missing Qto on IFC4 (`wall-pset-qto-missing-qto`) | Fail (expected) | — | — | **Rule gap / expected fail** — working as designed |
| T7 | `IfcRelAssociatesConstraint` rules | N/A in this suite | N/A | N/A | Honest non-support on IFC2x3 globally — not in this IDS |
| T8 | IFC4x3 parse on current IfcOpenShell | — | — | ✅ (tested) | — |

### Classification legend

| Class | Meaning | Action this week |
|---|---|---|
| **parser bug** | IfcOpenShell/IfcTester crashes or mis-reads valid entity graph | Fix + regression test |
| **rule gap** | Engine should detect planted defect but does not (IFC4/4x3) | Fix rule path; add case to `regression.json` |
| **honest non-support** | IFC release or input class outside declared support; fail-closed or degraded behavior is correct | **Document only** — do not fake pass |

---

## Suite-level inventory (open corpora profiles)

| Profile | Count | Claim level | Parser bugs found? |
|---|---|---|---|
| `regression` (fixture IDS↔IFC) | **7** | fixture regression | **None identified** — pins in [`regression.json`](../../samples/benchmarks/open-corpora/profiles/regression.json) |
| `regression-bsi` (buildingSMART TestCases) | **290** | open regression (CC BY-ND) | Not re-triaged this week — import gate in CI |
| IFC-Bench v2 smoke | 7/1026 scored | `open_bench_only` | Smoke pass — not full corpus triage |
| Sprint-2 synthetic | 15 cases | `synthetic_only` | N/A — planted defects |

**Week decision:** No (a) parser or (b) rule-gap code changes scheduled unless a new failing CI run proves a regression on IFC4/IFC4x3 pass fixtures. IFC2x3 quantity name divergence stays **documented honest non-support**.

---

## Known unplanted classes (cannot fix with open corpus)

These gaps are **not** parser bugs. They require customer data, license budget, or scope decisions.

| Class | Blocker | Why open corpus cannot plant it | RT / track |
|---|---|---|---|
| **Native DWG** | Proprietary format; fail-closed without ODA Sustaining | Open readers unreliable on RU/SPDS/xrefs; see [`dwg-blocker-memo-2026-08.md`](../dwg-blocker-memo-2026-08.md) | License / owner decision — **not** parser bug |
| **Customer expertise conclusions** | No open remark↔package pairs | EGRZ/registry metadata only; see [`expertise-corpus-scan-2026-08.md`](../datasets/expertise-corpus-scan-2026-08.md) | **RT-001** |
| **Customer-approved norm packs** | Draft/template ≠ approved | Open GOST text ≠ signed customer rule pack | **RT-002** |
| **Customer SLA** | Fixture timing ≠ production load | `regression` / fixture SLA is ms–seconds on tiny IFC | **RT-003** (also MEP federated scope) |
| **CDE-ready BCF** | T2 import not proven on customer CDE | BCF ZIP structural OK; CDE import **НЕ ДОКАЗАНО** | Integration ladder T5 |
| **MEP system clash (delivered)** | ENG_PARTIAL; `geometry_verified=False` | OSArch MEP IFC useful for rehearsal only | RT-003 |
| **Product accuracy >90%** | No adjudicated TP/FP corpus | All open benches explicitly ≠ L3 | RT-001 |

---

## IFC2x3 quantity check — explicit honesty statement

The IDS file [`wall-pset-qto.ids`](../../samples/ids/wall-pset-qto.ids) requires:

```xml
<propertySet><simpleValue>Qto_WallBaseQuantities</simpleValue></propertySet>
<baseName><simpleValue>Width</simpleValue></baseName>
```

The IFC2x3 fixture [`wall-pset-ifc2x3.ifc`](../../samples/ifc/wall-pset-ifc2x3.ifc) stores width under **`BaseQuantities`**, which is schema-correct for IFC2x3:

```
#10=IFCPROPERTYSET(...,'BaseQuantities',...,(#12));
#12=IFCPROPERTYSINGLEVALUE('Width',$,IFCLABEL('0.3'),$);
```

**Verdict:** If the engine does not map `Qto_WallBaseQuantities` → `BaseQuantities` on IFC2x3, that is **honest non-support / documented degradation**, not grounds to claim DWG-ready-style greenwash on cross-release Qto checks. The compatibility matrix already states: *«Quantity check falls back to BaseQuantities Pset matching; no false ERROR, emits INFO»*.

Parametric tests in [`test_ifc_release_compatibility.py`](../../backend/tests/test_ifc_release_compatibility.py) currently assert FireRating across releases; Qto cross-release behavior is documented in matrix + this triage.

---

## Recommended actions (documentation-only this week)

1. **Keep** IFC2x3 quantity divergence classified as honest non-support in customer-facing honesty surfaces.
2. **Do not** add silent pass for missing Qto on IFC4 (missing-qto fixture must keep failing).
3. **Do not** conflate BSI n=290 or fixture n=7 pass rate with product accuracy.
4. **Link** pilot intake to [`expertise-corpus-scan-2026-08.md`](../datasets/expertise-corpus-scan-2026-08.md) data request checklist for RT-001.
5. **Re-run** open corpora smoke only if pins change:

```bash
cd backend
python -m aerobim.tools.run_open_corpora_profiles --mode smoke
```

---

## Checkpoint

| Item | Status |
|---|---|
| Parser bugs on IFC4/IFC4x3 wall-pset suite | **None filed** |
| Rule gaps on pass fixtures | **None filed** |
| Honest non-support documented | **Yes** (IFC2x3 Qto naming) |
| RT-001/002/003 | **Open** |
| Checkpoint | **NO_GO** |
