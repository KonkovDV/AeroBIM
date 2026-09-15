---
title: "Поле «Прототип» — запуск и проверяемое поведение"
status: active
version: "1.1.0"
last_updated: "2026-09-15"
claim_boundary: >
  Runnable prototype on fixtures. Not customer корпус, not measured SLA,
  not product accuracy. Checkpoint GO; customer_go false; RT-001/002/003 OPEN.
---

# Прототип

Запускается из репозитория одной командой на **учебном комплекте**. Данных заказчика в дереве нет.

Review shell (не замена CLI): `frontend/` — `npm run dev` против API. По умолчанию `GET /v1/auth/bff` = 501; баннер ролей обязателен. Экспорт: HTML/JSON/BCF/PDF (простой PDF карты покрытия). Кнопки XLSX нет. Приём модели на жёстком профиле до 1,5 ГБ диском; SPF и вьюер — 256 МиБ. Текст замечания в BCF — два абзаца `[RU]` / `[EN]` в одном поле Description.

**Формула стадии (дословно; источник — [карточка речи для жюри](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки контура заказчика. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, двух разметчиков, подписанного профиля назначающей стороны и подтверждения импорта в СОД.

## Что запускается на чистом клоне (основной показ)

```bash
cd backend
pip install -e ".[dev,raster]"
python -m aerobim.tools.run_demo_ifc_acceptance_gate
```

На выходе — каталог `artifacts/ifc-acceptance-gate-demo/` (создаётся локально, в репозиторий не входит): `acceptance-gate.json`, `report.html`, `report.json`, `findings.bcfzip`.

Это **fixture-only**. HTML-снимок в [`../../docs/evidence/kt2-handoff-2026-08-11/`](../../docs/evidence/kt2-handoff-2026-08-11/) — архив прогона 11.08, а не живой показ.

Пакет КТ#3 и демо-день, если файлов заказчика нет. Одна команда:

```bash
python -m aerobim.tools.run_kt3_jury
```

Эквивалент двумя командами: `python -m aerobim.tools.run_demo_ifc_acceptance_gate` и `python -m aerobim.tools.run_kt3_without_customer`.  
Пакет без ожидания: `python -m aerobim.tools.run_kt3_without_customer`. Речь: [`../../docs/demo/KT3_JURY_FAQ_2026_08_25.md`](../../docs/demo/KT3_JURY_FAQ_2026_08_25.md). Замок: [`../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md`](../../docs/demo/DEMO_DAY_SPEECH_LOCK_2026_09.md). Трекер: [`../../docs/demo/KT3_TRACKER_SIX_TASKS_2026_08.md`](../../docs/demo/KT3_TRACKER_SIX_TASKS_2026_08.md). Сценарий: [`../../docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md`](../../docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md).

После `pip install -e ".[dev,raster]"` контракт клона для жюри — `pytest tests -q`: **0 failed**. Extra `pdf-agpl` и секреты публикационного denylist — только CI; без них тесты пропускаются. Локальный счётчик не заменяет [`runtime-baseline-latest.json`](../../docs/evidence/runtime-baseline-latest.json) (`attested_by=ci`).

## Что показывает находка

Прогон: IFC + IDS → находка с GUID элемента, идентификатором правила, парой expected/observed и ссылками на доказательства. `summary.passed` пишет только детерминированный контур (ADR-001). Блок `capabilities` перечисляет, что проверено, что пропущено, что `NOT_VERIFIED`.

| Вопрос | Ответ |
|---|---|
| Почему `summary.passed=false`? | В учебном комплекте заложены дефекты. Это ожидаемый отказ, не сбой демо. |
| Что такое finding? | Требование → правило → объект → evidence. Не акт экспертизы и не точность продукта. |
| Почему это не customer accuracy? | Комплекта заказчика канала в дереве нет (RT-001 OPEN). Учебный F1 / AABB n=6 / 27/1026 — другие контуры. |
| Что если обязательная проверка не прошла? | Capability `FAILED` роняет комплект. Молчание не считается успехом. |
| Доказывает ли BCF ZIP импорт в СОД? | Нет. Структурный архив T1 есть. Импорт в СОД заказчика — `NOT_VERIFIED` (это блокер, не код). |

## Дополнительные команды (не ядро показа)

| Класс | Команда | Граница |
|---|---|---|
| **Основной показ** | `python -m aerobim.tools.run_demo_ifc_acceptance_gate` | Учебный комплект; `summary.passed=false` ожидаем |
| **Демо-день** | `python -m aerobim.tools.run_kt3_jury` | Тот же учебный контур; GUID FireRating, не площадь |
| **P1** | `python -m aerobim.tools.run_demo_vertical_slice` | Оверлей на PDF. Не ядро вердикта |
| **Учебные часы** | `python -m aerobim.tools.measure_package_sla` | Fixture p95; `sla_pass` не переносится на заказчика |
| **Docker** | `python -m aerobim.tools.offline_bundle verify` | Пробный image-track; не комплект заказчика |

## Веб-интерфейс (P1, не показ КТ#2)

```bash
python scripts/run_review_shell.py
```

Просмотр IFC в 3D, наложение на 2D, список замечаний, правка текста экспертом. Это оболочка ревью, не замена живой команды.

## Что прототип делает честно

| Поведение | Почему это важно жюри |
|---|---|
| Пропуск обязательной проверки роняет комплект | «Нет находок» не значит «проверено» |
| Несовпадение схемы IFC и версии в IDS — ошибка | Чужая схема не проходит молча |
| Модели не меняют технический статус | Языковая или визуальная модель не может превратить отказ в успех |
| Воспроизводимость | Повторный прогон даёт тот же `reproducibility_hash` по детерминированным находкам |
| Конфликт документов не «разрешается» автоматически | Обе стороны и доказательства; решает эксперт |

## Границы прототипа

Чтение DWG и нативных RVT/NWD без конвертации — не реализовано. Системные коллизии MEP — `NOT_VERIFIED`. Импорт BCF в СОД заказчика — `NOT_VERIFIED`. Независимого расчётного решателя нет: сверяем переданные результаты с источниками. Компьютерное зрение и языковые модели только подсказывают.

Развёрнуто: [`../../docs/pilot-claim-boundary-2026.md`](../../docs/pilot-claim-boundary-2026.md).

## Учебные данные для прогона

[`../../samples/`](../../samples/) — учебные комплекты IFC, IDS, чертежей и спецификаций. Не выгрузка Renga и не комплект заказчика. Приложения ТЗ: [`../../samples/tz-appendix/README.md`](../../samples/tz-appendix/README.md). Стенка+IDS для показа FireRating: [`../../samples/benchmarks/project-package-wall-fire-rating.json`](../../samples/benchmarks/project-package-wall-fire-rating.json).
