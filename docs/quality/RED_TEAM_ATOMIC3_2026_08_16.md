---
title: "Round 9 — quis custodiet: аудит верификаторов и evidence-инструментов"
status: active
version: "1.1.0"
last_updated: "2026-08-16"
claim_boundary: "Original pass was audit-only. Disposition records remediations. Checkpoint NO_GO; RT-001/002/003 OPEN. Ninth round (IDs HD9-*)."
audited_head: "375109c + working tree"
auditor: "ZCode"
---

# Round 9 — кто проверяет проверяющих

## Находки

### HD9-VER-01 (LOW): верификатор релиза по умолчанию проверяет устаревший день

`tools/verify_release_evidence.py:302` — `--day` по умолчанию `"2026-08-06"`. Вызов без аргументов проверяет вчерашний снапшот и печатает «OK: release evidence consistent». Принцип «оператор должен помнить = будущий инцидент»: дефолт должен быть `latest` или требовать явную дату.

### HD9-VER-02 (INFO): `--no-complete` ослабляет требования молча

`:305-309` — флаг легитимно понижает полноту проверяемых гейтов (partial-day сценарий), но релаксация должна само-маркироваться в артефакте (`"complete": false` на верхнем уровне + строка в выводе), иначе relaxed-прогон неотличим от полного в логах.

### HD9-VER-03 (OK-CONFIRM): ядро верификаторов fail-closed

`verify_evidence_bundle.py:143` — `"ok": not errors` (аккумулятор ошибок, fail-closed), exit 0/1 строго по ok; подделка аттестации локально закрыта ранее (N-18: `--attested-by ci` удалён, только `GITHUB_ACTIONS`). Паттерн-свеп tools/ подтвердил: единственный fail-open в слое — HD8-TOOL-01 (MOEXP coverage).

## Реестр открытых после 9 раундов

HD8-TOOL-01 (evidence-генератор, первый в очереди) · HD7-IDS-03 (spec-truthiness) · HD7-IFC-01 (verify `_to_float`-skip) · HD2-UP-01 · HD3-BFF-01 · HDX-LINT-01 · HD2-RL-02 (by-design) · HD9-VER-01/02. Верификаторы как класс — целы; ловушки — операторские дефолты.

## Disposition (после Round 8 close-out)

HD8-TOOL-01 **FIXED** в working tree (`export_moexp_ids_coverage.py`, schema 1.2.0). HD7-IDS-03 / HD7-IFC-01 / HD2-UP-01 / HD3-BFF-01 не открывать. HD9-VER-01 **FIXED** (`--day` default `latest`). HD9-VER-02: `complete` уже в JSON; stdout помечает `complete=false`.
