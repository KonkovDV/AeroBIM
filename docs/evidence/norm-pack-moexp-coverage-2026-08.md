<!-- claims-lint: allow-file reason="Official MOEXP IDS engine coverage; fixture fail is not product accuracy" -->
# Official MOEXP IDS coverage (IfcTester)

**claim_level:** `official_ids_engine_coverage`
**customer_accuracy_not_established:** `True`
**closes_rt002_customer_profile:** `False`

Official GAU MO MosoblGosExpertiza IDS executed by IfcTester. Fixture IFC is not a MOEXP-compliant CIM. Pass/fail on the fixture is not product accuracy, not Samolet acceptance, and does not close RT-002 (customer-approved profile still absent). ICMM 3.3 has no published IDS.

Source: https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/

## Engine coverage (headline)

| Metric | Count |
| --- | ---: |
| IDS files | 24 |
| Specifications | 389 |
| Executable (IfcTester ran) | 389 |
| Unsupported facets | 0 |
| Load errors | 0 |

## Fixture probe (not CIM compliance)

Open fixture `samples/ifc/wall-pset-qto-pass.ifc`. Fail here means the spec ran and the wall fixture did not satisfy it.

| Metric | Count |
| --- | ---: |
| Pass on fixture | 0 |
| Fail on fixture | 389 |

## By domain

| Domain | files | specs | exec pass | exec fail | unsupported | load error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ad-uds | 2 | 82 | 0 | 82 | 0 | 0 |
| nis | 2 | 91 | 0 | 91 | 0 | 0 |
| oks | 20 | 216 | 0 | 216 | 0 | 0 |

## By pack kind (filename, not a new run)

`attributes` = published `Требования_…` IDS. `classification` = published `Проверка_КСИ_…` IDS.
This split does not mean CIM compliance. Engine coverage only.

| Kind | files | specs | exec pass | exec fail | unsupported | load error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| attributes | 12 | 206 | 0 | 206 | 0 | 0 |
| classification | 12 | 183 | 0 | 183 | 0 | 0 |
| other | 0 | 0 | 0 | 0 | 0 | 0 |

ICMM 3.3 is PDF-only on the TIM page as of 2026-08-13; no IDS listed.

Generated at: `2026-08-13T20:33:20.765514+00:00`
content_sha256: `6c00afc4d68a4c5152de45f6bb81c21b905608cbd6444e9d975c4700e91abb05`
machine: `{"platform": "Windows-11-10.0.26200-SP0", "python": "3.13.7", "machine": "AMD64", "system": "Windows"}`
