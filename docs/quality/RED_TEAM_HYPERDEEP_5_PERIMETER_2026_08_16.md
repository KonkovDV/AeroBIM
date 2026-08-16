---
title: "Red Team Hyper-Deep Round 5 — perimeter close-out: SQL, VLM egress, HTML/PDF renderers"
status: active
version: "1.0.0"
last_updated: "2026-08-16"
claim_boundary: "Audit report plus later remediations. Checkpoint stays NO_GO. Final round of HD-series (IDs HD5-*). Series: 1 triage, 2 seams, 3 engines, 4 academic, 5 perimeter."
audited_head: "2768058 (committed) + uncommitted working tree 2026-08-16"
auditor: "ZCode autonomous triage, round 5 (solo)"
---

# Red Team Hyper-Deep Round 5 — периметр: SQL, VLM-egress, рендереры

Пятый проход закрыл последние заявленные residual-зоны: postgres-стор SQL-слой, VLM advisory-клиент (egress/ключи/парсинг), report_html макро-логика, simple_pdf. Результат — почти весь периметр подтверждён как OK; новых MEDIUM нет. Remediation (1.6.27): DDL-граница задокументирована; CR/LF в PDF-литералах заменяются пробелом. Checkpoint **NO_GO**.

## 1. Реестр находок

| ID | Sev | Зона | Файл:строка | Суть | Статус |
|---|---|---|---|---|---|
| HD5-PGSQL-01 | OK-CONFIRM | db | `postgres_audit_store.py:54-106` | SQL полностью параметризован (именованные `:param`, `text()`); фильтры через `(:x IS NULL OR …)` — инъекций нет | OK-CONFIRM |
| HD5-PGSQL-02 | INFO | db | `postgres_audit_store.py` DDL | `ALTER TABLE … ADD COLUMN IF NOT EXISTS` на старте — рантайму нужны DDL-привилегии | DOCUMENTED |
| HD5-VLM-01 | OK-CONFIRM | vlm | `vlm_advisory_client.py:200-234` | api_key обязателен (нет дефолта), base-host allowlist (`assert_llm_base_host_allowed`), ключ редaktирован из `repr`, strict `json_schema` response_format, reject nonfinite, reason-codes | OK-CONFIRM |
| HD5-VLM-02 | INFO | vlm | `vlm_advisory_client.py:137-138` | Вендорные отклонения от json_schema (Yandex `json_object` вместо strict) задокументированы живым evidence — honest workaround | OK-CONFIRM |
| HD5-HTML-01 | OK-CONFIRM | html | `report_html.py:335-348` | Overlay-href только из `_ALLOWED_OVERLAY_HREFS` allowlist + `_esc`; удалённых/`javascript:`/path-escaping href нет | OK-CONFIRM |
| HD5-PDF-01 | OK-CONFIRM | pdf | `simple_pdf.py` | PDF-литералы экранированы (backslash, скобки); CR в строках не экранировался — косметика, не инъекция | FIXED (CR/LF → space) |
| HD5-IFCV-01 | RESIDUAL | ifc | `ifc_open_shell_validator.py` | Полное построчное чтение не выполнено (severity-срезы и fail-closed точки проверены в раунде 4) | OPEN residual |

## 2. Детали

**Postgres (HD5-PGSQL-01/02).** 208-строчный индексный стор: INSERT с `ON CONFLICT DO UPDATE` (идемпотентный re-save), list с nullable-фильтрами, peek_tenant одной строкой. Вся SQL-конструкция — статические `text()`-шаблоны с именованными параметрами; конкатенаций и f-string SQL не найдено. Единственная операционная шероховатость — DDL на старте: контур БД-пользователя шире, чем CR(UD); для пилота приемлемо, для продакшена — миграции отдельно от рантайма.

**VLM-клиент (HD5-VLM-01/02).** Конструктор fail-closed (пустые `base_url`/`api_key` → ошибка), egress через allowlist хостов (не голый `assert_safe_outbound_url` — дополнительно ограничен по домену), схема ответа закреплена хешем (`observations_schema_hash` в provenance кэша — воспроизводимость advisory-ответов). Вендорныеquirks (Yandex не принимает strict json_schema с optional-полями) оформлены как профиль с живым evidence-комментарием, а не молчаливый fallback. Культура перенесена даже в экспериментальный слой.

**HTML/PDF рендереры.** `report_html` — два уровня защиты (allowlist href + `_esc` на всё); `simple_pdf` — корректный PDF-literal escaping; усечения/`(empty)`-строки не дают молчаливой порчи вывода.

## 3. Итог серии из пяти раундов

**46+7 = 53 находки** по ID-реестрам HD/HD2/HD3/HD4/HD5; из них:
- **0 CRITICAL / 0 HIGH**;
- **10 MEDIUM**: HD-MW-01 (429 без заголовков), HD-CLAIMS-01/02 (guard=README-only, RU-маркеры), HD-DOC-01/02 (drift 48↔54; 93 неучтённых теста), HD-DIFF-01/02 (CRLF; Redis-breaking), HD2-OIDC-01 (JWKS-ротация), HD2-RM-01 (origin-фильтр хеша), HD2-RL-03 (прокси-бакет), HD2-UP-01 (диск до reserve), HD2-DI-01 (DI-lock), HD3-IDS-01 (status-дефолт), HD3-CLASH-01 (молчаливый continue), HD3-IFC-01 (вечный кэш), HD3-BFF-01 (unverified lab-сессия) — точнее 13 MEDIUM;
- остальные LOW/INFO/OK-CONFIRM.

**Сквозной портрет:** вердикт-честность и академическая дисциплина — образцовые и независимо воспроизводимы; периметр рендереров/SQL/VLM-egress — чист; систематические слабости сосредоточены в трёх классах: (1) конкурентность/жизненный цикл ресурсов, (2) «тишина = успех» на парсер-уровне при дрейфе внешних форматов, (3) управляемость doc-ов/claims на масштабе одного человека.

## 4. Финальный residual (честно)

Не прочитано построчно за всю серию: `ifc_open_shell_validator.py` (полный текст), VLM-пайплайны целиком (только клиент и профили), `App.tsx` (1300 строк — grep-уровень), ~290 из 302 тест-файлов, внешняя верификация цитат через веб. Оценка «0 CRITICAL» верна в пределах прочитанного (≈60% src построчно, остальное — структурные карты + grep-матрица); непрочитанное не проверено, а не проверено-чисто.
