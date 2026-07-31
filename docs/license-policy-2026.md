---
title: "License policy 2026"
status: active
version: "1.0.0"
date: "2026-07-31"
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

## LIC-001 (PyMuPDF) — дерево решений

VERIFIED 2026-07-31: `pymupdf==1.27.2.3` — «Dual Licensed - GNU AFFERO GPL 3.0
or Artifex Commercial License», обязательная core-зависимость, серверный путь.

| Опция | Стоимость | Эффект | Статус |
|---|---|---|---|
| A. Коммерческая лицензия Artifex | деньги, договор | снимает блокер, код не трогаем | ждёт юр./бюджет |
| B. Миграция text-бэкенда (pypdfium2 — Apache/BSD-класс; pdfminer.six — MIT) | инженерия: порт + адаптер + тесты функц. эквивалентности (текст, координаты, RU/EN) | снимает блокер для text path; raster-crop путь мигрирует отдельно | не начата; seam уже изолирован |
| C. Изоляция в optional extra `[pdf-agpl]` с fail-closed degrade | средняя | core становится AGPL-free; PDF-функции честно skipped без extra | не начата |
| D. AGPL-компилаенс всего продукта | открыть всё под AGPL | конфликт с текущим MIT-позиционированием | отвергается по умолчанию |

Решение принимает владелец проекта после юридической консультации; до решения
LIC-001 остаётся OPEN в CRITICAL_BLOCKERS и checkpoint-статус не улучшается.

## Не заявляем (Claims Lock)

«AeroBIM целиком под MIT»; «нет лицензионных рисков»; «AGPL не применим» (без
юр. заключения). Разрешено: «MIT для собственного кода; сторонние компоненты —
под своими лицензиями (см. inventory)».
