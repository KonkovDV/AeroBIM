<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# Конкурентная матрица AeroBIM (помеченный анализ)

**Дата:** 2026-08-04  
**claim_level:** competitive_analysis_only — **не** product accuracy  
**closes_rt001:** false  

Это не утверждение «мы лучше Solibri». Это оси, где гипотеза AeroBIM отличима, и оси, где зрелые продукты объективно сильнее.

## Матрица

| Ось | Solibri | Autodesk Navisworks | BIMcollab | AeroBIM (сегодня) |
|---|---|---|---|---|
| Доступность в РФ / контур ПП 1236 (госнужды / госучастие) | иностранный продукт | иностранный продукт | иностранный продукт | **российский код, закрытый контур** |
| Кросс-документная сверка (чертёж ↔ модель ↔ ТЗ ↔ расчёт) | частично / IDS-центрично | слабо | issue-centric | **да (fixture / eng)** |
| Provenance до листа PDF и GUID в IFC на каждой находке | ограниченно | ограниченно | частично | **да (enforced persist)** |
| Fail-closed: пропуск обязательной проверки блокирует `passed` | нет (типичный green-path) | нет | н/п | **да (Shared-gate)** |
| Доказуемый инвариант: advisory LLM OFF==ON для вердикта | нет | нет | нет | **да (ADR-001 / WP-02)** |
| Норм-пак заказчика с версией, клаузой, журналом | ограниченно | нет | нет | **схема готова; RT-002 OPEN** |
| Зрелость model checking / экосистема | **высокая** | **высокая** | средняя (issues) | ниже |
| Доля рынка / узнаваемость | высокая | высокая | средняя | **нулевая** |
| Native DWG / CDE-ready BCF import | сильнее | сильнее | сильнее в issues | **не заявляется** |

## Как читать

1. Две нижние строки (зрелость / доля рынка) — сознательные уступки: без них таблица выглядит как маркетинг.  
2. Трудно копируемый актив при пилоте: **норм-пак заказчика с историей экспертных подтверждений** — даже при MIT на ядре (см. ADR-002 open-core).  
3. Главный конкурент по смыслу — **внутренняя разработка заказчика**, не Solibri. Внешнее решение имеет смысл, если быстрее и дешевле проверяет гипотезу на пилоте.

## Источники позиционирования (не accuracy)

- Claims Lock / Checkpoint NO_GO — [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md)  
- ADR-001 verdict ownership — [`docs/architecture/ADR-001-verdict-ownership-2026.md`](../architecture/ADR-001-verdict-ownership-2026.md)  
- ADR-002 open-core (**accepted**) — architecture docs  
- Место в контуре Самолёта — [`docs/docs.md`](../docs.md) §2  

## Запрещено выводить из этой таблицы

- «точность >90%», «MEP delivered», «CDE-ready», «мы победили Solibri».
