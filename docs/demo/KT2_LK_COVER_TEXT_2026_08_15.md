<!-- claims-lint: allow-file reason="KT#2 LK paste text; TZ 90%/30min as non-claims; NO_GO" -->
---
title: "КТ#2 — текст в личный кабинет Техлаб"
date: "2026-08-15"
claim_boundary: "Cabinet paste only. Fixture/open-bench ≠ customer accuracy. Checkpoint NO_GO. Not DWG-ready. Not MEP delivered."
---

# Текст для ЛК (вставить как описание решения)

Инфопост Техлаба: до **20 августа** идёт КТ#2. Команду в ЛК **не** править. Обновлять только решение: отозвать → обновить страницу → «Загрузить решение».

Ниже — готовый текст. Не вставлять черновик `Desktop/AeroBIM/1.txt` (устаревшие 1 980 тестов / 46·71·59 / «шесть дней»). Не вставлять `AeroBIM.pdf` (заявка Industrix, апрель 2026, другой контур). Не вставлять `2.txt` как решение (инвест-нарратив июля). ТЗ Самолёта у заказчика уже есть — не грузить PDF ТЗ как «наше решение».

---

AeroBIM — детерминированная проверка комплекта проектной документации (IFC + IDS + PDF/офис + cross-doc), задача №7 Техлаб / «Самолёт».

Стадия: **доработка**. Checkpoint **NO_GO**. Валидация эффективности и внедрение у заказчика ещё не начались. Три блокера открыты: корпус ПД+экспертиза (RT-001), подписанный нормативный пакет Самолёта (RT-002), измеренный федеративный MEP-clash (RT-003). Открытые бенчи и учебный пакет Renga эти блокеры не закрывают.

Прототип (ссылка): https://github.com/KonkovDV/AeroBIM  
Первые 30 секунд: live CLI Acceptance Gate + честная строка «без разметки заказчиком цифры не публикуем».  
Живой срез (sell-path): `cd backend && python -m aerobim.tools.run_demo_ifc_acceptance_gate` → `artifacts/ifc-acceptance-gate-demo/acceptance-gate.json`. Overlay PDF (P1, если время): `python -m aerobim.tools.run_demo_vertical_slice` → `artifacts/vertical-slice-demo/report.html` (`#kt2-overlay`). Overlay = pypdfium2. Демо-IFC в репозитории — IfcOpenShell fixture, не выгрузка Renga и не модель Самолёта.

Что можно смотреть сейчас (fixture / open-bench, не точность продукта):

- Live CLI: fail-closed finding с `finding_id` / `source_id` / `evidence_refs`, `summary.passed=false`.
- Матрица IFC2X3 / IFC4 / IFC4X3 (n=20, кернел): findings 5 / 4 / 6; `passed=false`; на мелких стенах `clash=skipped`; IFC4X3 `ids=failed` = fail-closed `ifcVersion`, не дефект продукта.
- IFC-Bench v2: countable **27/1026**, pin ok, `open_bench_only`. Не 514 false-pass.
- AEC-Bench: 196 задач в инвентаре; Harbor agent **NOT_RUN**; drawing-reading false-pass **NOT_MEASURED**.
- ПНСТ 909: снимок **18/22** IDS от 05.08 (ToS GO на агрегат). Свежий 18/22 на этой машине не выдумывали: полный extract усечён до header-sample.
- Ishigaki-IDS-Bench: 166 gold XML, document-audit processable. Нет IFC. Это не F1 из статьи и не точность продукта.
- IDS МОГЭ / АГР Москвы / СПб ЦГЭ — в git; это не профиль приёмки Самолёта.
- VLM (Qwen / Kimi) — advisory only. Вердикт модель не ставит и не снимает.

Как читаем ТЗ №7 (критерии «точность >90%» и «до 30 минут»): это целевые критерии приёмки **на корпусе заказчика**, не заявленная точность AeroBIM. В ТЗ не определены полнота vs точность попаданий, корпус, разметчики и учёт пропусков. Наш протокол измерения: `docs/pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`. Нативный DWG в коде = FAILED (не тихая дыра). SLA ≤30 мин на fixture не публикуем как customer KPI.

Просим на КТ#2 не раунд и не GO, а слот + один раздел комплекта с фактическим заключением (обезличенно / NDA / on-prem). Сентябрь — КТ#3, итоговое решение; победителей определяют заказчики.

Команда AeroBIM

---

**Ссылка прототипа в поле ЛК:** `https://github.com/KonkovDV/AeroBIM`  
**Видео:** по скрипту [`KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md`](KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md), файл локально, в git не класть.  
**Повторно прикрепить** (инфопост разрешает): cover [`KT2_HANDOFF_COVER_2026_08_11.md`](KT2_HANDOFF_COVER_2026_08_11.md), матрица IFC, hunt log.
