<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
# Конкурентная матрица AeroBIM (помеченный анализ)

**Дата:** 2026-08-04 · **refresh:** 2026-08-16 (AI-review / ИСП РАН / BIM Inspector; клин: [`WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md`](WEDGE_FREEZE_EVIDENCE_LAYER_2026_08_16.md))  
**claim_level:** competitive_analysis_only — **не** product accuracy  
**closes_rt001:** false  

Это не утверждение «мы лучше Solibri». Это оси, где гипотеза AeroBIM отличима, и оси, где зрелые продукты объективно сильнее.

Публичный стек и вектор: [`../samolet.md`](../samolet.md).  
Пять решений Задачи 07 (поля Анализ 3): [`../demo/KT2_TASK07_COMPARISON_2026_08.md`](../demo/KT2_TASK07_COMPARISON_2026_08.md) — не эта таблица Solibri/Navisworks.

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

Solibri CheckPoint (cloud + ACC/Procore, AI-assistant beta — публичный срез 2025–2026) не отменяет строку Solibri: зрелый model QA. AeroBIM не утверждает «делаем то, чего Solibri не умеет вообще». Ниша — cross-modal evidence / provenance / fail-closed / on-prem API, не глубина BIM-правил. Revizto / ACC / Navisworks / Bentley iTwin — конкуренты за процесс замечаний и lifecycle, не замена клина IFC+IDS+пакет.

## Как читать

1. Две нижние строки (зрелость / доля рынка) — сознательные уступки: без них таблица выглядит как маркетинг.  
2. Трудно копируемый актив при пилоте: **норм-пак заказчика с историей экспертных подтверждений** — даже при MIT на ядре (см. ADR-002 open-core).  
3. Главный конкурент по смыслу — **внутренняя разработка заказчика + Tangl**, не Solibri. Внешнее решение имеет смысл, если быстрее и дешевле проверяет гипотезу на пилоте.

## Российский контур (срез 14.08.2026)

Западная таблица выше отвечает на «почему не Solibri». Эта — на «кто уже стоит у девелопера».

| Игрок | Что закрывает | Где сильнее AeroBIM | Где мы отличимы (гипотеза, не accuracy) | Метка |
|---|---|---|---|---|
| **Tangl Control** | Проверка BIM-модели, clash, атрибуты; Самолёт — стратегический клиент BIM-данных | Зрелость model checking | **Комплект** (чертёж↔IFC↔ТЗ↔расчёт), fail-closed IDS, provenance листа | `[П]` tangl.cloud/projects/samolet/ |
| **Tangl Value** | Объёмы / CIM→BoQ; ГАЛС с 2022 (primary) | Смета из модели | Не наш слой — не конкурируем | `[П]` tangl.cloud |
| **Самолёт 10D** | СОД, качество площадки, цикл стройки; с сен 2025 фокус inward | Маршрут документа, 38 модулей | Не платформа. Модуль QA комплекта *до* площадки | `[П]` TAdviser / CIO.osp |
| **А101 / Vitro-CAD** | CDE, согласование ПД и Revit; ПМЭФ-2026 × МИК — полигон **зрелых** ИТ | Документооборот проектирования | Второй логотип только после измеримого пилота; сейчас early для их фильтра | `[П]` |
| **ГАЛС / Sarex** | СОД + чек-листы АФК/ПД/РД (кейс 07.2026) | Чек-лист в маршруте | Не утверждать Tangl Control / Pilot-BIM без первички. Клин слабее Самолёта | `[П]` sarex.io |
| **ПИК / PikTools / BIM Inspector** | Автоматизация Revit + внутренний checker перед МГЭ | Production-контур и данные ПИК | Самолёт на Renga — чужой Revit-стек не копируем; не «мы единственные, кто проверяет BIM» | `[П]` bimteam.ru/bi · Habr ПИК Digital |
| **SmartIDS / VALIDBIM (ИСП РАН)** | Требования → IDS; IFC verification | Академический контур IDS/IFC | Сшивка требование↔модель↔документ↔журнал, не только свойства IFC | `[П]` ispras.ru |
| **ТИМ.Нейро / NormaChecker** | Нормативный корпус (заявлен больше) | Размер норм | RT-002 OPEN; наш ров — пакет + journal, не «600 норм на слайде» | `[Ф]`/`[Н]` |

## AI-review / 2D (срез 16.08.2026)

Не прямой BIM-checker. Опасны на демо: быстрый визуальный эффект без IFC.

| Игрок | Что закрывает | Где сильнее AeroBIM | Где мы отличимы (гипотеза) | Метка |
|---|---|---|---|---|
| **Structured AI / Nomic / Specset / Helonic** | PDF/чертежи, RFI, codes, цитаты | Скорость 2D-шоу | Не продаём «магию PDF»; продаём измеримый IFC/IDS слой + provenance | `[П]` публичные сайты |
| **Togal.AI** | Takeoff, измерение, сравнение листов | 2D quantity | Не наш первый клин | `[П]` |
| **Document Crunch / Trimble** | Контрактный / проектный риск | Юридический NLP | Не IFC/геометрия | `[П]` |
| **VitruAI** | Revit + нормы; финал у лицензиата | Revit-native | Самолёт — Renga/IFC; мы не заменяем эксперта | `[П]` |
| **IfcOpenShell / IfcTester / BIMTester / open IFC Model Checker** | Бесплатная база IFC/IDS | Зрелость парсера | Не конкурент: это наш runtime; лицензии — LIC-001 | `[П]` docs.ifcopenshell.org |

**Правило речи:** «Tangl проверяет модель; мы — комплект. 10D ведёт документ; мы не заменяем 10D.»

## Источники позиционирования (не accuracy)

- Claims Lock / Checkpoint NO_GO — [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md)  
- ADR-001 verdict ownership — [`docs/architecture/ADR-001-verdict-ownership-2026.md`](../architecture/ADR-001-verdict-ownership-2026.md)  
- ADR-002 open-core (**accepted**) — architecture docs  
- Место в контуре Самолёта — [`docs/docs.md`](../docs.md) §2  

## Запрещено выводить из этой таблицы

- «точность >90%», «MEP delivered», «CDE-ready», «мы победили Solibri».
