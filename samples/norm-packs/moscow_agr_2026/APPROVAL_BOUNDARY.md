<!-- claims-lint: allow-file reason="Approval-boundary SSOT; RT-002 split; forbidden phrases as non-claims; Checkpoint NO_GO" -->

# Approval boundary — `moscow_agr_2026`

Checkpoint **NO_GO**. This pack does **not** paint RT-002 CLOSED without the a/b split. It does **not** unfreeze the CUT `moscow_agr` DI port.

## Verbatim boundary

City published the CIM AGR filing requirements (DGP order № ДГП-Р-1/26/64-16-6/26, effective 2026-04-02, plus the public stroimprosto IDS). The city is the **publisher of the NPA / IDS**, not AeroBIM’s customer, and did not endorse the product. Samolet internals remain out of scope.

RT-002 is closed in **regulatory** volume (`RT-002a`): this pack has `status=approved`, a full `approval` object, city as `approved_by`, and a content `pack_hash`. RT-002 stays open in **corporate** volume (`RT-002b`): no Samolet-signed EIR / `pack_hash`.

JSON schema vocabulary maps pack `status=approved` onto the engine badge `customer_approved`. That badge here means **city-as-publisher**, not “Samolet signed this pack”. Do not say “customer stack = Renga”. Do not say product accuracy >90%. Do not say RT-003 is closed. Clash/MEP stay honest SKIPPED under `AEROBIM_SIGNOFF_PROFILE=moscow_agr_2026`.

This pack is a **measurement ruler**, not a commercial AGR self-check. From 2026-06-29 Moscow requires a free positive city CIM report at AGR filing; AeroBIM does not sell a substitute for that portal.

Schema 2.0.0 `expert_confirmation_journal` is present and **empty**: the JSON encoding of city IDS properties is not expert-confirmed. Deterministic v2 rules therefore do not enter positive checking until a journal `confirmed` entry exists. That is fail-closed, not a hidden green pass.

## What this pack is

- Small AR subset of **real** Moscow AGR IDS properties (`RusSet_*` on IfcSpace / IfcWall) already vendored under `samples/ids/moscow-agr/`.
- Not 389 invented MOGE JSON rules. Not a copy of `samples/ids/moexp/`.
- Class-1 AGR exchange checks (IFC4 RV, no proxy, filename, 500 MB, TEP XML) stay in `agr_exchange_checks.py`. They are not this pack.

## What this pack is not

- Not a Samolet acceptance profile.
- Not GrK art. 49 expertise.
- Not an AGR certificate.
- Not CDE-ready BCF.
- Not MEP delivered.
- Not the frozen `moscow_agr` DI port restored.
