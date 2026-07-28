---
title: "AeroBIM Hybrid AI — Threat Model (2026-07-28)"
status: active
version: "1.0.0"
last_updated: "2026-07-28"
claim_boundary: "Threat model of the hybrid routing design. No safety guarantee claimed. Checkpoint NO_GO."
tags: [aerobim, hybrid-ai, threat-model, security]
---

# Hybrid AI — модель угроз

Companion к `HYBRID_AI_ARCHITECTURE_2026_07_28.md`. Активы: исходные IFC/чертежи/
расчёты, customer/NDA-данные, tenant-изоляция, ключи/токены, provenance, вердикт.
Границы доверия: локальный контур (доверенный) → частный контур (условно) →
публичный API (недоверенный). **Ни одно смягчение не объявляется гарантией.**

| # | Угроза | Вектор | Смягчение | Остаточный риск / уровень |
|---|---|---|---|---|
| T1 | Утечка CONFIDENTIAL/RESTRICTED в публичный API | ошибочный/злонамеренный маршрут | fail-closed policy engine; запрет public для C/R/SECRET; egress-лог | зависит от корректности классификации — **запланировано (Wave 2)** |
| T2 | Prompt injection (текст/изображение/BCF/OCR/кэш/ответ) | недоверенные данные как инструкции | output-as-data; строгая схема (fail-closed); капы; игнор+**surfacing** control-полей | покрыто тестами (image+text+schema); **код+тест** |
| T3 | Модель как маршрутизатор/выбор инструмента | «используй другую модель/вызови инструмент» | router не читает секреты, не меняет policy/verdict/ACL; server-tools off | **запланировано (Wave 2 инварианты)** |
| T4 | Кросс-tenant утечка (отчёт/IFC/кэш/BCF/audit/masked) | общий namespace, подмена tenant/namespace | object-ACL→404; fail-closed изоляция кэша; tenant из проверенной личности | покрыто (ACL/кэш); masked/audit — **P1** |
| T5 | Re-identification после маскирования | структура/геометрия/редкие значения/имена систем | Privacy Guard + тесты утечки/re-id/обхода; маска ≠ анонимность | **P1 (не реализовано)** |
| T6 | Эксфильтрация через ответ модели | ответ содержит verdict/severity/route/tool | forbidden-fields в схеме; вердикт вне контура; verification layer | покрыто (schema/grounding); **код+тест** |
| T7 | Подмена вердикта через Hybrid AI | mask/route/timeout/schema failure → PASS | вердикт только детерминированный движок; OFF==ON | покрыто (OFF==ON); маршрут-сбои — **интеграц. тесты P1** |
| T8 | Утечка секретов в логи/аудит | reasoning_content, ключи, токены | не логировать секреты; типизированный AuditEvent без секретов | код (аудит); типизация — **Wave 3** |
| T9 | Отравление кэша / устаревший снапшот | подмена/старый ответ | golden-hash integrity; act-grade ключ; tenant-scoped | покрыто (кэш); **код+тест** |
| T10 | DoS / bomb / flood | zip/XML-bomb, flood наблюдений, длинный payload | byte-cap; per-region budget; drop-not-whole | покрыто; **код+тест** |

**Жёсткое правило:** любое смягчение из «запланировано/P1» — **не доказано**;
до внедрения + отрицательных тестов соответствующий класс данных обрабатывается
fail-closed (BLOCKED). Маскирование **снижает раскрытие, но не доказывает анонимность**.
