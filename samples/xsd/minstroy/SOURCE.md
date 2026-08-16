# Official MinStroy XML schemas (EGRZ / ECPE intake)

**Catalog:** https://minstroyrf.gov.ru/tim/xml-skhemy/  
**Retrieved:** 2026-08-14 (evening re-probe of subsections `p9_4/` / `p12_2/` plus survey-assignment / survey-report catalog pages)  
**Claim:** published MinStroy XSD for *intake* pre-check (well-formed XML, declared root, XSD where XMLSchema11 can load the file, including a load-time strip of duplicate `xml:id` on `xs:documentation` for PZ/ZnP). Not GrK art. 49 expertise. Not a remark corpus. Not УКЭП. Does **not** close RT-001.

AeroBIM does not claim authorship. XSD files are redistributed as published. Zips (XSD + XSL + PDF) stay out of git.

## Honesty — versions vs ECPE

From **11.06.2026** ECPE accepts Пояснительная записка **01.07** and Задание на проектирование **01.01** only. Citation: [ГАУ Мордовия, 10.06.2026](https://www.xn--13-6kclkmgo9almibr3n.xn--p1ai/useful-information/769/).

The **main** catalog listing still highlights PZ 1.05 (28.12.2024) and ZnP 01.00. The **subsection** pages `p9_4/` / `p9_5/` and `p12_2/` also offer zips whose members are `explanatorynote-01-07.xsd` and `DesignAssignment-01-01.xsd`. Those member folders still contain `dev_`. The XSD `SchemaVersion` attributes are **fixed** `01.07` / `01.01`. Catalog primary in this repo is those two files.

Do not treat a third-party write-up (for example k-css.ru naming `explanatorynote-01-07.xsd`) as the source. Source is minstroyrf.gov.ru.

## Parser honesty

PZ / ZnP / conclusion declare `vc:minVersion="1.1"`. Survey-assignment and geological-report XSDs are XML Schema 1.0 (no `vc:minVersion`); XMLSchema11 still loads them as published.

| File | XMLSchema11 as published | After stripping `xml:id` on documentation |
| --- | --- | --- |
| `conclusion-01-03.xsd` | loads; root `Conclusion` | n/a (no xml:id) |
| `explanatorynote-01-07.xsd` | **fails** (`duplicated xs:ID value 'Name'`) | loads; empty fixture fails XSD (missing `SchemaVersion`) |
| `DesignAssignment-01-01.xsd` | same duplicate xml:id failure | loads; empty `<Document/>` fails XSD |
| `explanatorynote-01-05.xsd` / `01-06` / `DesignAssignment-01-00.xsd` | same xml:id failure | not the ECPE in-force row |
| `EngineeringSurveysTask-01-00.xsd` | loads; root `EngineeringSurveysTask` | n/a (no duplicate xml:id blocker) |
| `GeologicalReport-01-00.xsd` | loads; root `GeologicalReport` | n/a (no duplicate xml:id blocker) |

Fail-closed: do not treat XMLSchema10 empty-elements as pass. The documentation `xml:id` strip is a **parser workaround**; git keeps the official bytes.

## Files in git (XSD only)

| File | Role | SHA-256 | Bytes |
| --- | --- | --- | ---: |
| `conclusion-01-03.xsd` | ECPE / catalog match | `46387fa5b4d41f7fad64ff67e8d9aa0b48c6d59864b2eca2acc4c9822aba90ec` | 336542 |
| `explanatorynote-01-07.xsd` | **ECPE in-force**; catalog `p9_4` zip member | `742dc8ec7f2df425b27fd59d419f3d01e4f25f53025475f9e71f7f4f45459df4` | 586987 |
| `DesignAssignment-01-01.xsd` | **ECPE in-force**; catalog `p12_2` zip member | `38ff89664f1c8c3bd8fef9366d1ee747aa3313ada6c32dc026d5658d3c040be5` | 579951 |
| `explanatorynote-01-06.xsd` | previous named listing (`версия 01.06.zip`) | `e3fbc7b338d2b5a7d88855d41904cea5077e681b804489c017f3017823a12569` | 594624 |
| `explanatorynote-01-05.xsd` | previous main-listing 1.05 | `6002c961b155322b52ec64462eadb2c58049a0ad7f4411372b4e1f4b432f5f58` | 573278 |
| `DesignAssignment-01-00.xsd` | previous main-listing 01.00 | `f566de807cc3f74b807f0498dfd9e31948d14bc7c4146a4b9c1df1f8e2964b23` | 544958 |
| `EngineeringSurveysTask-01-00.xsd` | catalog survey assignment 01.00 | `7da19458da8d4201f7b42d3ecc858e18f191c6112f2fed0dcf90a2eb22b3b112` | 250229 |
| `GeologicalReport-01-00.xsd` | catalog survey report zip; XSD root is geological | `b6d55df9621c34ada95420347397b32e8d926e80218736c3ee75dad6c8618b9e` | 370274 |

## Source zips (not vendored; `.local/minstroy-xml/`)

| Zip | SHA-256 | Bytes | Notes |
| --- | --- | ---: | --- |
| conclusion V1_03 | `565f409d425124ee5b31c083dcfc650ea18d3f753d05020d8f479d2cdb133418` | 1119229 | catalog V1_03.zip |
| PZ 01.07 member zip (`p9_4`) | `cae4032fdf12b7176104a5dc20aee474d1e8ceb1be51c96ec190293a22500545` | 1078647 | folder `explanatorynote-dev_explanatorynote_v_1_07/` |
| PZ `версия 01.06.zip` | `a88dec2cb6fb14dad9e087c0a496d1f93ee7516414384e5e6f07e73afdd3b075` | 1404743 | named 01.06 |
| ZnP 01.01 member zip (`p12_2`) | `b86fd4f2d9fd180036d442d3326c87d1d9262701fbd1d006be98595cb4025ee3` | 42462554 | includes a 71 MB PDF; **XSD only** in git |
| PZ 1.05 / ZnP 01-00 | previous | — | still on the main listing |

Zips contained XSD + XSL + PDF. **No official instance XML.** Fail fixtures under `fixtures/` are synthetic. There is **no pass fixture**.

## Construction-stage catalog gap

MinStroy TIM news of **07.08.2026** named construction-stage XML schemas (instrumental inspection protocol, sample-selection protocol, GSN notices; listed as in force from **05.11.2026**) and a survey-assignment schema (listed as in force from **03.10.2026**). The 14.08.2026 catalog scrape used here found downloadable zips for **survey assignment** and **survey report** (geological XSD root). Construction-stage XSD files were **not** present as catalog members in that scrape. This repo does **not** invent those files.

`GeologicalReport` is the published root for the survey-report zip. That is engineering-geological, not a generic all-discipline survey report.

## Not RT-001 CLOSED

Matching the ECPE *schema version* and failing empty XML at the door is not a paired PD + expertise remark + dual κ/α + held-out FN. Product function: `egrz_intake_precheck`. Checkpoint **NO_GO**.
