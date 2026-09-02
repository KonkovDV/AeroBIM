<!-- claims-lint: allow-file reason="Jury-pack Red Team triage; roles not FIO; unpack counts off TIER0; NO_GO" -->
---
title: "Jury-pack Red Team triage — 2026-09-01"
date: "2026-09-01"
last_updated: "2026-09-01"
status: active
version: "1.0.3"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  KILL/HOLD/ACCEPT over public GitHub surfaces a sitting member opens first.
  Roles not FIO. Unpack fingerprint counts stay off TIER0. Not pack processed.
  Not sitting-member OSINT in git. Engineering pins stay, not as a jury exhibit.
  Checkpoint NO_GO.
---

# Триаж поверхностей жюри (01.09.2026)

Машина: `python -c "from aerobim.domain.jury_pack_triage import jury_pack_triage_snapshot"`.

Отборочная комиссия №7: [брифы кресел](MIK_SEAT_BRIEFS_2026_08.md) — **роли, не ФИО**. Три кресла партнёра **по согласованию**.

Инженерные пины инвентаря канала (census / family / local max-pass) **не** карта жюри и **не** exhibit. Карта: [`../TIER0_INDEX.md`](../TIER0_INDEX.md).

Checkpoint **`NO_GO`**. `detected_count: 0`. `processed: false`. Семь задач Техлаба — **Uncertain**.

Связанные: [`TRACKER_EIGHT_TASKS_2026_08.md`](TRACKER_EIGHT_TASKS_2026_08.md) · [`KT3_IN_REPO_WORKPLAN_2026_08_27.md`](KT3_IN_REPO_WORKPLAN_2026_08_27.md) · [`INTERPRETATION_USE_LEDGER_2026_08.md`](INTERPRETATION_USE_LEDGER_2026_08.md) · [`FORMAT_INGEST_TRIAGE_2026_09.md`](FORMAT_INGEST_TRIAGE_2026_09.md) · [`UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md`](UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md).

## Этот проход (KILL / HOLD / ACCEPT)

| ID | Атака | Тормоз |
|---|---|---|
| RT-JURY-FIO | Закоммитить ФИО сидящих или OSINT-био в публичное дерево | Брифы — роли; три кресла партнёра по согласованию; OA-2 |
| RT-JURY-HOMONYM | Открытые однофамильцы = подтверждённый состав | Кресла партнёра остаются по согласованию; не привязывать речь к чужой биографии |
| RT-JURY-TRACKER-NAME | Личное имя трекера в git-пути или snapshot | TRACKER_EIGHT_TASKS_2026_08; KT3_TRACKER_SIX_TASKS; в snapshot нет ключа person |
| RT-JURY-TIER0-CENSUS | Цифры unpack / DWG / RVT на TIER0 или docs.md | Census и family — инженерные пины, не exhibit жюри |
| RT-JURY-TIER0-SHORTLIST | Счётчики Office-shortlist на карточке восьми задач | TRACKER_EIGHT SIG-06: shortlist ≠ MATCH без этих счётчиков |
| RT-JURY-PROCESSED | Любой локальный инвентарь = пакет обработан | `processed=false`; `publishable_finding_count=0` |
| RT-JURY-TANGL | AeroBIM как замена Tangl креслу BIM | Бриф: 10D-атрибуты; Tangl — слой модели; мы — шов документов |
| RT-JURY-GIGACHAT | Процессные заметки вендор-чата на SSOT восьми задач | SSOT: несинхронизированные копии чата не используются; имени вендора нет |
| RT-JURY-CHANNEL-BRAND | Партнёрский бренд в имени public-файла max-pass | Переименовано в CHANNEL_LOCAL_MAX_PASS; не exhibit жюри |
| RT-JURY-OSINT-GIT | Трек OSINT-вектора партнёра или прочей кухни сессии | Файл вектора в gitignore; unpublished-list honesty lock |
| RT-JURY-LOCAL-PIN | Локально сгенерированный IFC/runtime pin как `attested_by=ci` | Pre-push предупреждает; `attested_by=ci` только; локальные тайминги не стейджим |
| RT-JURY-GIB | Несжатые байт-итоги NDA-дерева на поверхности жюри | `uncompressed_gib_in_git=false`; majority — boolean |
| RT-JURY-QUESTION-EXHIBIT | Неотправленный вопросник заказчику на TIER0 | Черновик в `partners/`; TIER0 больше не перечисляет |
| RT-JURY-OA-EXHIBIT | OWNER_ACTIONS как exhibit уже сделанной работы | Список владельца снят с TIER0; строки не marked done |
| RT-JURY-MEETS | Семейства ⇒ Meets/Does-not семи задач Техлаба | Criterion **Uncertain**; local max-pass — не вердикт |
| RT-JURY-ENG-PINS | Удалить census JSON из git, чтобы исчез тормоз «не processed» | Пины оставить; пометить не exhibit; счётчики не на TIER0 |
| RT-JURY-DENYLIST | Добавить фамилии комиссии в kitchen denylist этим коммитом | HMAC-пин — секрет CI; ротация секретов вне полосы |
| RT-JURY-SEATS-ROLES | На карте нет брифов ролей — речь выдумывает ФИО | MIK_SEAT_BRIEFS на TIER0; оговорка про ФИО есть |
| RT-JURY-RENAME | Личные имена трекера остаются в `git ls-files` | Honesty lock запрещает старые path-токены трекера/канала |
| RT-JURY-TIER0-SHRINK | TIER0 всё ещё рекламирует census / family / local max-pass / SIG-01 volume | Эти файлы сняты с TIER0; intro говорит не exhibit |
| RT-JURY-OSINT-IGNORED | OSINT-вектор сессии — отслеживаемый файл GitHub | Вектор в gitignore; unpublished-list honesty lock |
| RT-JURY-NOT-EXHIBIT | Инженерные пины выглядят exhibit, потому что TIER0 их перечислял | Intro TIER0: census / family / local max-pass — не карта жюри |
| RT-JURY-SPG-HOP | Клик с TIER0 / восьми задач на консалтинговый пин 49% ТИМ | Пин остаётся; имя файла снято с поверхностей жюри |
| RT-JURY-UI-LIVE | Hop с UI-пина TIER0 на «рабочее место сдано» / Checkpoint GO — нельзя | Пин: review shell; ноутбук жюри = CLI |
| RT-JURY-TZ-UI-DONE | Строка матрицы ТЗ Web UI = done как exhibit сдачи | Строка **partial**; SSOT — UI-пин |

## Что чинить в речи и git на этом проходе

1. **Не называть состав комиссии.** Роли и брифы; три кресла партнёра могут не сесть.
2. **Не цитировать census-счётчики** на карте жюри, в IUA-таблице и в DATA_STATEMENT.
3. **Не говорить «пакет обработан»** и не подменять Tangl.
4. **Не коммитить** локальный IFC/runtime pin как `attested_by=ci`.
5. **Не давать hop** с карты жюри на консалтинговый пин с рыночными %. Имя файла не на TIER0 и не в связанных ссылках восьми задач.
6. **Не читать** review shell или строку «Web UI» матрицы ТЗ как сдачу рабочего места. Показ жюри = CLI.

Не добавлять фамилии в denylist без ротации CI-секрета. Не удалять инженерные пины.

Checkpoint **`NO_GO`**.
