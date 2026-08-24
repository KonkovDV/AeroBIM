<!-- claims-lint: allow-file reason="City AGR example rehearsal; not PD pack; RT stay OPEN" -->
---
title: "Moscow AGR city examples — local rehearsal"
date: 2026-08-23
claim_level: moscow_agr_city_example_rehearsal
claim_boundary: >-
  City-published AGR CIM examples (stroimprosto.mos.ru cim-agr). Not a PD pack: no sheets, TZ, two revisions, calculations, or expertise remarks. Not a Samolet-signed profile. Class-1 AGR exchange + official IDS engine coverage only. Checkpoint NO_GO.
closes_rt001: false
closes_rt002b: false
closes_rt003: false
checkpoint: NO_GO
---

# Moscow AGR city examples

Official IFCs from the city article, plus already-vendored IDS/TEP/Vedomost. 
**Not** a PD pack. **Not** Samolet. Clash/MEP stay SKIPPED under 
`moscow_agr_2026`. Injector is not run. TEP sidecar is the official 
published example reused for every IFC (not a per-model TEP). IDS 
files are role-matched (ПС→ПС, БиО→БиО, АР→Общие+МССК).

- status: **RUN**
- reason: n/a
- IFC evaluated: **5**
- exchange-clean IFC: **3**
- injector_ran: `False`
- content_sha256: `6541005a4acbe1b0096f5d87ab9ec3c43ea0db67ba607d262667b604d20d880e`

```bash
cd backend
python -m aerobim.tools.fetch_moscow_agr_city_examples
python -m aerobim.tools.run_moscow_agr_city_examples
```
