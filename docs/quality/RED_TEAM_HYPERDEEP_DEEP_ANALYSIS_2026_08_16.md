---
title: "Red Team Hyper-Deep — углублённый итоговый анализ (пять раундов)"
status: active
version: "1.0.0"
last_updated: "2026-08-16"
claim_boundary: >-
  Auditor narrative after HD1–HD5. Scores are culture grades, not product
  accuracy, SLA, MEP delivered, CDE-ready, or Checkpoint GO.
  Checkpoint stays NO_GO (RT-001 / RT-002 / RT-003 OPEN).
  Section 7 lists the audit's priority plan as diagnosed; working-tree status
  is in §7.1 — do not treat the original plan as still open.
audited_head: "working tree 2026-08-16 after HD1–HD5 remediations"
auditor: "ZCode autonomous triage, deep analysis (solo)"
---

# Углублённый итоговый анализ AeroBIM

По материалам пяти раундов: 53 находки, ~60% исходников построчно, отчёты HD→HD5 в `docs/quality/`. Это мнение аудитора по культуре инженерии, не коммерческий GO.

## 1. Вердикт

AeroBIM — инженерно зрелый проект с нетипичной для индустрии культурой доказательной честности, на границе «законченный инженерный артефакт / непроверенный продакшен». Сильнейшая сторона — не код сам по себе, а система механизмов, не дающих себе лгать. Слабейшая — не ошибки, а слепые зоны, которые fixture-режим принципиально не проявляет: ресурсы, конкурентность, дрейф внешних форматов.

| Вертикаль | Оценка аудитора | Не путать с |
|---|---|---|
| Вердикт-контур и методология | 9–9.5/10 | не точность на корпусе заказчика |
| Безопасность и тестирование | 8–8.5/10 | не внешний pentest |
| Надёжность в конкурентной эксплуатации | 6/10 | класс остаётся после точечных фиксов |
| Управляемость процессов на масштабе | 6/10 | поверхность docs/CLI всё ещё широкая |

Ноль критических уязвимостей **в прочитанном**. Checkpoint **`NO_GO`**.

## 2. Архитектура

Трёхслойный hexagon: чистый домен (вердикты, находки, provenance, норм-паки, hybrid-контур), application с оркестраторами по контурам (`INGESTION` → `DETERMINISTIC_VALIDATION` → `AI_ADVISORY` → `EVIDENCE_REPORTING`), инфраструктура адаптеров за DI. React + web-ifc и CLI как научный аппарат — не оценка фронтенда построчно (`App.tsx` остаётся grep-уровнем).

Ключевой факт: граница deterministic / advisory проведена механикой. `DETERMINISTIC_VALIDATION` — единственный писатель `summary.passed`; LLM проходит `DeterminismGate` (демоция advisory → INFO). Проверено чтением вердикт-пути, перечислением сайтов `Severity.ERROR` (ни один в advisory-адаптерах) и монотонностью решётки исходов. Инвариант держится как **конвенция + gate + тесты**, не как изоляция типов (HD4-INV-02).

## 3. Честность как инфраструктура

Четыре контура (механический fail-closed, доказательный hash/manifest/baseline, процессуальный claims-lock / mutation / Red Team, академический Wilson/TOST / HMAC / errata DOI) — главный актив для жюри: diffs и артефакты, не обещания. Одновременно это главная нагрузка (§6).

## 4. Три класса слабостей (диагноз раундов)

Паттерны важнее отдельных багов: они предсказывают, где всплывут следующие. **Перечисленные экземпляры** из плана §7 в working tree закрыты; **классы** не исчезли.

| Класс | Смысл | Экземпляры аудита | Working tree |
|---|---|---|---|
| А. Тишина = успех на парсере | Защита от явного отказа движка, не от заикания формата | HD3-IDS-01 `status` default True; HD3-CLASH-01 silent continue; IDS mojibake | IDS missing status → SKIPPED/ERROR; malformed clash → failed. Класс жив на следующем поле, которое движок перестанет присылать |
| Б. Конкурентность / ресурсы | Не видно на фикстурах | DI без lock; JWKS без refetch; вечный IFC/TokenVault; quota до reserve; stale O_EXCL | RLock; JWKS kid-refetch + 30s cooldown; IFC LRU(8); TokenVault LRU(4096); reserve-ahead + stale hold reconcile; stale lock steal. Redis vs in-process window — documented |
| В. Знаковая поверхность | Честные документы, слабая машина согласованности | guard=README-only; 48↔54; 93 теста; ручные цитаты | scan 4 файлов + RU-маркеры; vitest 54; `tests_unaccounted`; DOI-twin lint. Поверхность CLI/docs по-прежнему широкая |

## 5. Жизненный цикл

NO_GO до закрытия RT-001/002/003 — правильная позиция: блокеры **evidentiary** (корпус ПД РФ, подписанный профиль, измеренный MEP-clash), не «код сырой». Код не должен закрывать их прокси-цифрами. Fixture GO ≠ Checkpoint GO.

Волна HD-hardening лежит в working tree (не закоммичена, пока оператор не попросит). Это не рыночный GO.

## 6. Стратегический риск

Дисбаланс производящей мощности и пропускной способности одного сопровождающего. Drift SSOT — симптом. Remediation сузил каналы (claims scan, DOI twins, baseline unaccounted); не заменяет второго инженера и не сокращает поверхность сама.

## 7. Приоритетный план аудита (как диагностирован)

Пункты 1–5 аудитора — «день работы перед внешним аудитором». Ниже — не повторная очередь работ, а сверка с деревом.

### 7.1 Статус в working tree

| План аудитора | ID | Статус |
|---|---|---|
| Убрать default True у IDS `status` | HD3-IDS-01 | FIXED |
| `origin=advisory` вне reproducibility-hash | HD2-RM-01 | FIXED |
| LRU IFC-моделей | HD3-IFC-01 | FIXED (cap 8) |
| JWKS refetch-on-miss | HD2-OIDC-01 | FIXED |
| Lock в DI-resolve | HD2-DI-01 | FIXED (`RLock`; plain `Lock` deadlocked boot) |
| Middleware + Retry-After | HD-MW-01 / HD2-RL-04 | FIXED |
| RU-маркеры + scanned_files | HD-CLAIMS-01/02 | FIXED (4 файла) |
| baseline ↔ README + учёт тестов | HD-DOC-01/02 | FIXED |
| Quota / detection швы | HD2-UP-01, HD3-CLASH-01 | FIXED (quota hold reconcile; clash GUID required) |

Оставшийся эффект на доверие — не эти пять строк, а **экспозиция**: реальный объём, гонки, дрейф зависимостей, RT-001/002/003.

## 8. Одна характеристика

Проект построил иммунную систему против самообмана — и она работает; пишет математику, воспроизводимую до целого, и цитаты по errata. Оставшиеся проблемы — шрамы, которых ещё нет: реальный объём, конкурентность, дрейф зависимостей. От «продакшен-экспозиции» его отличает не качество изготовления, а отсутствие этой экспозиции — и он сам это формулирует: **NO_GO**, Fixture GO ≠ Checkpoint GO.

Ограничение: ~40% исходников — карты и grep, не построчное чтение (residual в HD5 §4). «0 критических» — в пределах прочитанного. По плотности паттернов скрытый fail-open вердикта не следует.
