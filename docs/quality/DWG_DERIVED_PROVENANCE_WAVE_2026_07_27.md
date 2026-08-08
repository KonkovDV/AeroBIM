<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "DWG derived-provenance hash verification + conversion-loss QA (MVP steps 3–6)"
status: done
version: "1.1.0"
last_updated: "2026-07-27"
claim_boundary: "Верифицированная derived-пара документирует, к какому файлу относится анализ; dwg_dxf никогда OK; native DWG остаётся MISSING. Checkpoint NO_GO."
---

# Wave S — DWG derived-provenance hash verification (2026-07-27)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Attestation ≠ evidence | in-toto (Torres-Arias et al., USENIX Security 2019) / SLSA provenance: заявленная supply-chain-атестация имеет вес только при криптографической проверке связки артефактов |
| Derivation semantics | W3C PROV-DM `prov:wasDerivedFrom` — производный артефакт трассируется к источнику явным отношением, а не заменяет его |
| Информационный менеджмент | ISO 19650-1 §3.3: information container identity/status — анализ обязан указывать, к какому контейнеру относится результат |
| Round-trip fidelity | Практика conformance-тестирования CAD-обмена (ISO 10303 STEP / bSI software certification): качество конвертации доказывается детерминированным диффом содержимого, а не заявлением конвертера |
| Внутренний прецедент | Wave H (2026-07-25, `verify_bcf_t2_evidence`): hashes.json пересчитывается, чужой hash-пак не может включить claim — тот же паттерн |

## Gap closed

`FOUR_DIRECTION_GAP_ANALYSIS` §1.3 требовал для DWG conversion MVP шаги
3 (регистрация пары `source_dwg_sha256↔derived_*_sha256`), 5 (fail-closed при
неуспехе конвертации) и 6 (маркировка «результат относится к производному
файлу»). Скаффолд `DerivedCadProvenance` существовал, но: (а) sidecar
принимался **на веру** — заявленные хэши не пересчитывались; (б) derived-route
не был подключён к analyze-пути — DWG с честной конвертацией всё равно валил
пакет без возможности зарегистрировать замену.

## Delivered (code + test)

- `domain/derived_cad_provenance.py`:
  - `verify_derived_cad_provenance` — пересчёт SHA-256 **обоих** файлов пары;
    обязательны путь+хэш источника и derived + известный формат; path jail к
    каталогу пакета (объявленный путь не может выйти за directory sidecar'а);
    любой пробел → `verified=False` c перечнем mismatches;
  - `verify_derived_provenance_sidecar` — нечитаемый sidecar fail-closed
    (никогда чистый skip);
  - `write_derived_provenance_sidecar` / `find_derived_provenance_sidecar` —
    конвенция `<name>.dwg.derived-provenance.json`;
  - `DERIVED_NOT_NATIVE_CLAIM` — граница формулировки в самом payload.
- `application/services/package_ingestion.py::run_cad_ingest`:
  - DWG c **верифицированным** sidecar → derived route:
    `dwg_dxf=NOT_VERIFIED` («hash-verified derived substitute … native DWG not
    parsed»), INFO-issue `AEROBIM-CAD-DWG-DERIVED` с evidence_refs
    (sidecar + оба sha256) — эксперт видит, к какому файлу относится результат;
  - невалидный sidecar **строже**, чем его отсутствие: WARNING с mismatches +
    `dwg_dxf=FAILED` (заявленная, но недоказуемая конвертация = красный флаг);
  - без sidecar — прежний RT-D путь (unsupported DWG валит пакет; sibling DXF
    не маскирует).
- `tools/register_dwg_conversion.py` (+ console script
  `aerobim-register-dwg-conversion`) — оператор регистрирует пару после
  **внешней** конвертации; sidecar сразу re-верифицируется; exit 1 при
  неуспехе; абсолютные пути независимы от CWD.
- **QA потерь конвертации (шаг 4 §1.3 / пороги §1.4)** —
  `domain/cad_conversion_qa.py`:
  - `evaluate_conversion_loss` — детерминированный дифф согласованного
    инвентаря листов/слоёв против наблюдаемого (case-insensitive,
    сохранение объявленного написания); политика
    `ConversionQaPolicy(max_layer_loss_ratio, missing_sheet_is_failure)` —
    строгий дефолт (любая потеря = failed);
  - `evaluate_conversion_qa_section` — вердикт **всегда пересчитывается**
    из инвентарей sidecar'а: рукописный `"status": "ok"` не может
    обелить потери; malformed-секция fail-closed;
  - интеграция: QA `failed` отклоняет derived-пару (`dwg_dxf=FAILED`);
    QA `warning` сохраняет route + WARNING `AEROBIM-CAD-DWG-QA` с loss report
    для эксперта; CLI принимает `--expected-sheet/--expected-layer/
    --observed-*/--max-layer-loss-ratio`.
- `tests/test_dwg_derived_provenance.py` — **20 тестов**: валидная пара; tamper
  derived-файла; обязательность обоих хэшей; path-jail escape; нечитаемый
  sidecar; naming convention; UC-путь verified→NOT_VERIFIED (и никогда OK) с
  INFO+evidence_refs; tampered→FAILED+WARNING; без sidecar→legacy FAILED;
  CLI roundtrip + exit 1; QA: ok/failed/warning пороги, whitewash-защита,
  malformed fail-closed, UC-путь warning-route и failed-reject, CLI с QA.

## Explicitly NOT claimed

- Native DWG остаётся `MISSING`; `dwg_dxf=ok` по-прежнему запрещён honesty
  gate — derived route даёт максимум `NOT_VERIFIED`.
- QA сравнивает **заявленные** инвентари (согласованный список от
  заказчика vs выход конвертера): автоматическое извлечение слоёв из
  бинарного DWG невозможно без парсера — инвентарь источника даёт
  заказчик/конвертер, мы его детерминированно сверяем.
- Никакой строки «DWG поддерживается»: анализ относится к производному
  файлу, что явно записано в отчёте и в claim_boundary sidecar'а.

## Gate evidence (2026-07-27 local)

`ruff format/check` PASS (350 files) · `mypy src` 207 files PASS ·
`pytest tests -q` **1149 passed, 7 skipped**.
