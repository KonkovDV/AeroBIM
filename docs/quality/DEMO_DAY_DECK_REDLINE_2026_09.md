<!-- claims-lint: allow-file reason="Demo-day deck redline; quotes of forbidden deck claims under KILL; NO_GO" -->
---
title: "Demo-day deck redline — 13.09.2026 vs git pins (14.09)"
date: "2026-09-15"
last_updated: "2026-09-15"
status: active
version: "1.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
claim_boundary: >
  Red Team of the 13.09 demo-day deck against git pins. Quotes of the deck
  are attacks, not licensed speech. Checkpoint GO; customer_go false.
---

# Красная черта деки 13.09

Машина: `python -c "from aerobim.domain.demo_day_speech_lock import demo_day_speech_lock_snapshot"`.
Речь: [`../demo/DEMO_DAY_SPEECH_LOCK_2026_09.md`](../demo/DEMO_DAY_SPEECH_LOCK_2026_09.md).
Дека вне git (рабочий стол). Этот файл — сверка, не exhibit жюри.

| ID | Атака | Тормоз |
|---|---|---|
| RT-DEMO-TRL5 | УГТ-5 / TRL 5 на обложке как ГОСТ Р 58048 | Самооценка TRL 4; `trl_5_claimed` False |
| RT-DEMO-837-CUSTOMER | 837 IfcClash как АР ↔ ИОС заказчика | IFC-Bench duplex; сети в IFC канала = 0 |
| RT-DEMO-GRID-ALL-PACKS | Оси не выгружены во всём комплекте | IfcGrid 0 / 13 / 53; нули только у EDM-экспорта |
| RT-DEMO-AREA-GEOMETRY | Площади считаем по геометрии IfcSpace | QTO only; `space_area_from_geometry=not_implemented` |
| RT-DEMO-F1-043 | AECV 0,43 как macro F1 | `macro_extended`; не F1; open_bench_only |
| RT-DEMO-N62-AS-N | n ≥ 62 как подписанный размер выборки | 62 = power_design; recommended_n = 111 |
| RT-DEMO-KR-17 | 4/24 округлить до 17 % | Headline ≈16,7 % (4/24); coverage_map_only |
| RT-DEMO-389-IN-50 | 389 спецификаций в 50 файлах | 389 = 24 файла МОГЭ; 50 файлов = 847 spec |
| RT-DEMO-SSO-READY | SSO / OIDC / BFF на IdP как готово | `GET /v1/auth/bff` = 501 по умолчанию |
| RT-DEMO-BCF-CDE | Замечания уже в реестре СОД через BCF | T1 ZIP; `cde_import=NOT_VERIFIED` |
| RT-DEMO-REGISTRY-NOW | Реестр российского ПО как статус | CLAIMS_LOCK: только план с датой подачи |
| RT-DEMO-PACK-PROCESSED | «Прогнали комплект — вот что нашли» как дефекты заказчика | `processed=false`; publishable finding count = 0 |
| RT-DEMO-IFC4-EXAMPLE | Пример IFC4 ADD2 без пометки «учебный» | На канале только IFC2X3 |
| RT-DEMO-NWD-NATIVE | Три NWD-федерации «приняты» / прочитаны | Носители есть; native fail-closed |
| RT-DEMO-REVISION-DUPES | Дубликаты ревизий как класс находки | 4 IFC в unpack — копии обёртки; класс не запинен |
| RT-DEMO-MYPY-FILECOUNT | «mypy: N файлов» | Пин CI: mypy PASS; поля числа файлов нет |
| RT-DEMO-AGR-DATE | Самопроверка ЦИМ с 23.06.2026 | Пин репозитория: **29.06.2026** |
| RT-DEMO-WEIGHTS-PDF | Веса Приложения 3 как attested CI | PDF не в git; 30/20/20/20/10 совпали с десктопным сканом 14.09; не `attested_by=ci` |
| RT-DEMO-ESCROW-NAMED | % переноса срока партнёра как наш эффект | Контекст рынка; E1–E5 не подписаны |
| RT-DEMO-UGT-ON-COVER | Цифра уровня готовности на обложке | Обложка: шов + трасса. TRL 4 — в приложении, как самооценка |
| RT-DEMO-AI-NOT-NEEDED | «ИИ не нужна» | ADR-001: вердикт детерминированный; ИИ — извлечение и подсказки |
| RT-DEMO-VALIDATOR-SURNAME | Выдуманная фамилия валидатора | Роль: инженер нормоконтроля / ГИП комплекта |
| RT-DEMO-LEGAL-DATE | Дата регистрации юрлица | Не выдумывать; вход Фонда — команда физлиц |
| RT-DEMO-GANTT | Диаграмма Ганта как план сдачи | Публичный backlog — GitHub Issues |
| RT-DEMO-SLA-PASS | `sla_pass true` как SLA заказчика | `claim_level=fixture_only`; `customer_go` false; schema id ≠ claim |
| RT-DEMO-RECALL-100 | 10/10 seam-clean как полнота продукта | `synthetic_only`; Wilson lower 0.722 |

Pack-letter IfcSpace (engineering pin, не слайд жюри): 10 599 + 1 339 + 4 214 = 16 152; NetFloorArea = 0. Источник: [`../evidence/deep-study-carrier-facts-2026-08.md`](../evidence/deep-study-carrier-facts-2026-08.md).

KEEP без нового кода: счётчики CI из runtime-baseline; лимиты 1,5 ГБ / 256 МиБ / 500 МБ; E1–E5 дословно; тесты ACL / SSRF / service-token.

Checkpoint **`GO`**; `customer_go` false.
