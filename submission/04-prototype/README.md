---
title: "Поле «Прототип» — запуск и проверяемое поведение"
status: active
version: "1.0.2"
last_updated: "2026-08-17"
claim_boundary: >
  Runnable prototype on fixtures. Not customer корпус, not measured SLA,
  not product accuracy. Checkpoint NO_GO; RT-001/002/003 OPEN.
---

# Прототип

Запускается из репозитория одной командой на **учебном комплекте**. Данных заказчика в дереве нет.

**Формула стадии (дословно, SSOT [`../../docs/demo/KT2_JURY_FAQ_2026_08_12.md`](../../docs/demo/KT2_JURY_FAQ_2026_08_12.md)):** Мы на стадии доработки. Одна команда показывает находку с доказательствами на учебном комплекте. Валидация эффективности и внедрение ещё не начались. `NO_GO` сохраняется, пока нет корпуса Самолёта, двух разметчиков, подписанного профиля приёмки и подтверждения импорта в СОД.

## Что запускается на чистом клоне (основной показ)

```bash
cd backend
pip install -e ".[dev,raster]"
python -m aerobim.tools.run_demo_ifc_acceptance_gate
```

На выходе — `artifacts/ifc-acceptance-gate-demo/` (каталог gitignore, в форму не кладётся): `acceptance-gate.json`, `report.html`, `report.json`, `findings.bcfzip`.

Это **fixture-only**. Снимок HTML из [`../../docs/evidence/kt2-handoff-2026-08-11/`](../../docs/evidence/kt2-handoff-2026-08-11/) демонстрацией не является. Не открывать `wall-guid/report.html` как overlay.

## Что показывает находка

Прогон: IFC + IDS → находка с GUID элемента, идентификатором правила, парой expected/observed и ссылками на доказательства. `summary.passed` пишет только детерминированный контур (ADR-001). Блок `capabilities` перечисляет, что проверено, что пропущено, что `NOT_VERIFIED`.

| Вопрос | Ответ |
|---|---|
| Почему `summary.passed=false`? | В учебном комплекте заложены дефекты. Это ожидаемый отказ, не сбой демо. |
| Что такое finding? | Требование → правило → объект → evidence. Не акт экспертизы и не точность продукта. |
| Почему это не customer accuracy? | Комплекта Самолёта в дереве нет (RT-001 OPEN). Учебный F1 / AABB n=6 / 27/1026 — другие контуры. |
| Что если обязательная проверка не прошла? | Capability `FAILED` роняет комплект. Молчание не считается успехом. |
| Доказывает ли BCF ZIP импорт в СОД? | Нет. Структурный архив T1 есть. Импорт в СОД заказчика — `NOT_VERIFIED` (RT, не код). |

## Дополнительные команды (не ядро показа)

Не ставить рядом с основным демо как «тоже продукт». Каждая строка — отдельный класс.

| Класс | Команда | Граница |
|---|---|---|
| **Основной показ** | `python -m aerobim.tools.run_demo_ifc_acceptance_gate` | Fixture-only; `summary.passed=false` ожидаем |
| **P1, fixture-only** | `python -m aerobim.tools.run_demo_vertical_slice` | Оверлей на PDF. Не ядро вердикта |
| **protocol-only, fixture-only** | `python -m aerobim.tools.measure_package_sla` | Порядок времени на учебном комплекте. Не SLA заказчика |
| **protocol-only, fixture-only** | `python -m aerobim.tools.evaluate_detection_precision` | TP/FP на размеченной синтетике. Не точность Самолёта |
| **honesty** | `python -m aerobim.tools.validate_dwg_toolchain` | Чтение DWG без конвертации — `NOT_IMPLEMENTED` |
| **protocol-only** | `python -m aerobim.tools.verify_kt2_handoff` | Самопроверка пакета КТ#2. Не customer evidence |

## Веб-интерфейс (P1, не показ КТ#2)

```bash
cd frontend
npm ci
npm run dev
```

Просмотр IFC в 3D, наложение на 2D, список замечаний, правка текста экспертом. Это оболочка ревью, не замена live CLI.

API: живая схема на `GET /openapi.json` запущенного сервиса (генерируется `backend/scripts/export_openapi.py`; дампы в git не коммитятся). Загрузка — `POST /v1/uploads`.

## Что прототип делает честно

| Поведение | Почему это важно жюри |
|---|---|
| Пропуск обязательной проверки роняет комплект | «Нет находок» не значит «проверено» |
| Несовпадение схемы IFC и версии в IDS — ошибка | Чужая схема не проходит молча |
| Модели не меняют технический статус | Языковая или визуальная модель не может превратить отказ в успех |
| Воспроизводимость | Повторный прогон даёт тот же `reproducibility_hash` по детерминированным находкам |
| Конфликт документов не «разрешается» автоматически | Обе стороны и доказательства; решает эксперт |

## Границы прототипа

Чтение DWG без конвертации — не реализовано. Системные коллизии MEP — `NOT_VERIFIED`. Импорт BCF в СОД заказчика — `NOT_VERIFIED`. Независимого расчётного решателя нет: сверяем переданные результаты с источниками. Компьютерное зрение и языковые модели только подсказывают.

Развёрнуто: [`../../docs/pilot-claim-boundary-2026.md`](../../docs/pilot-claim-boundary-2026.md).

## Учебные данные для прогона

[`../../samples/`](../../samples/) — учебные комплекты IFC, IDS, чертежей и спецификаций. Не выгрузка Renga и не комплект Самолёта. Приложения ТЗ: [`../../samples/tz-appendix/README.md`](../../samples/tz-appendix/README.md).
