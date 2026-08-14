---
title: "License policy 2026"
status: active
version: "1.1.0"
date: "2026-08-14"
claim_boundary: "Инженерная политика, не юридическое заключение. LIC-001 требует юриста."
---

# License policy (AeroBIM)

SSOT данных: [`audit/dependency_license_inventory.json`](../audit/dependency_license_inventory.json).
CI-гейты: `backend/tests/test_dependency_license_gate.py` (классификация обязательна;
unknown блокирует) и `backend/tests/test_license_isolation_guard.py`
(copyleft-движки не выходят за infrastructure/tools).

## Правила

1. **MIT — только для собственного кода AeroBIM.** Любая публичная формулировка
   лицензии обязана содержать disclosure сторонних компонентов (Claims Lock v3).
2. Каждая shipped-зависимость (core + optional extras + frontend runtime) имеет
   запись в inventory: версия, метаданные лицензии, SPDX-оценка, risk_class,
   `legal_review_required`.
3. Risk-классы: `permissive` (MIT/BSD/Apache/PSF) — свободно;
   `weak_copyleft` (LGPL/MPL) — не модифицировать, disclosure, юр. проверка
   рекомендована; `strong_copyleft_or_commercial` (AGPL/GPL/dual-commercial) —
   **release-blocking** до юридического решения; `unknown` — блокирует всегда.
4. Copyleft-движки импортируются **только** из `infrastructure/adapters` и
   `tools` — domain/application/presentation/core остаются чистыми (guard-тест).
   Это фиксирует поверхность миграции.
5. Новая зависимость без классификации в inventory = красный CI.

## Две полосы (14.08.2026)

Показ **Самолёту** может использовать copyleft **входные файлы** локально.
Публичный продукт, Docker, GitHub и **остальные** заказчики — без токсичных лицензий.

| Полоса | Где | Можно | Нельзя |
|---|---|---|---|
| **public_mit** (default, CI, Docker, другие заказчики) | git + `requirements-lock.txt` | MIT-код; LGPL IfcOpenShell за infrastructure/tools; optional `pdf-agpl` **не** в runtime lock | Вендорить GPLv3 IFC; линковать LibreDWG; тащить AGPL в Docker |
| **samolet_demo_local** | gitignored `.local/` на машине демо | Читать GPLv3 IFC-Bench (`4351`, `ettenheim_gis`, `hitos`, `samuel_macalister_sample_house`) | Коммитить эти файлы; включать флаг в CI; закрывать RT-001 |

Включение:

```bash
python -m aerobim.tools.fetch_ifc_bench_v2 --from-dir <checkout> --include-gplv3 --samolet-demo-copyleft
python -m aerobim.tools.run_federated_mep_inventory --samolet-demo-copyleft
```

Вторая команда **не** пишет GPL-строки в `docs/evidence/`. LibreDWG **не** линкуется: для показа Самолёту заказчик даёт IFC/PDF/A; CAD capability на `.dwg` остаётся FAILED.

Это не юридическое заключение. Checkpoint остаётся **NO_GO**.

## LIC-001 (PyMuPDF) — дерево решений

VERIFIED 2026-07-31 lock SSOT historically `pymupdf==1.28.0` (dual AGPL/Artifex).
**Owner decision 2026-07-31: Option B** — production core PDF path uses
`pypdfium2` + `pdfminer.six` (+ Pillow). PyMuPDF remains only as optional
`pdf-agpl` (dev/tools), absent from `requirements-lock.txt` / Docker runtime.

| Опция | Стоимость | Эффект | Статус |
|---|---|---|---|
| A. Коммерческая лицензия Artifex | деньги, договор | снимает блокер, код не трогаем | не выбрана |
| B. Миграция (pypdfium2 / pdfminer.six) | инженерия | core PDF без AGPL | **SELECTED / DONE (eng)** |
| C. Изоляция в optional extra | средняя | core AGPL-free с degrade | superseded by B (extra retained as `pdf-agpl`) |
| D. AGPL-комплаенс всего продукта | открыть всё под AGPL | конфликт с MIT-позиционированием | отвергается |

LIC-001 в CRITICAL_BLOCKERS: **ENGINEERING_CLEARED_FOR_CORE_PDF** — residual:
optional AGPL extra must not be reintroduced into runtime lock without owner
decision; disclosure still required for all third-party components.

## Не заявляем (Claims Lock)

«AeroBIM целиком под MIT»; «нет лицензионных рисков»; «AGPL не применим» (без
юр. заключения). Разрешено: «MIT для собственного кода; сторонние компоненты —
под своими лицензиями (см. inventory)».
