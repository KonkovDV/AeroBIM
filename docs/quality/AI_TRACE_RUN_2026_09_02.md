<!-- claims-lint: allow-file reason="AI-trace run log 2026-09-02; placeholder classification; not product accuracy; NO_GO" -->
---
title: "AI-trace run — 2026-09-02"
status: active
version: "1.0.0"
last_updated: "2026-09-02"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Editorial run log. Not product accuracy. Checkpoint GO; customer_go false.
  Owner chose variant A (move lit-radar prompt to docs/ai/).
---

# AI-trace run — 02.09.2026

Скан: markdown вне `.venv` / `.local` / `node_modules` / `RED_TEAM_*`.  
Регекс плейсхолдеров: `TODO|FIXME|TBD|N/A|{journal}|your_api_key|lorem ipsum|<placeholder>` (**не** `\bNA\b`: иначе ловит `-na-` в URL).

## Мета-голос

| Файл:строка | Класс | Решение |
|---|---|---|
| `docs/quality/ACADEMIC_LIT_REVIEW_2026_09.md` §4 (было) | **ARTEFACT** | Перенесено в [`../ai/ACADEMIC_LIT_RADAR.md`](../ai/ACADEMIC_LIT_RADAR.md); в обзоре однострочная ссылка |
| `docs/quality/AI_TRACE_AUDIT_2026_09.md` встроенный промт очистки | **ARTEFACT** | Перенесено в [`../ai/AI_ARTEFACT_CLEANER.md`](../ai/AI_ARTEFACT_CLEANER.md) |
| `docs/quality/RED_TEAM_ATOMIC4_*` Kitchen dump | LEGITIMATE | Не трогали (серия RED_TEAM, unpublished) |

Чат-наполнители: **0**. Галлюцинационные маркеры: **0**.

## Плейсхолдеры (69 хитов этого прогона; аудит называл 64)

**ARTEFACT: 0.** Ни `{journal}`, ни lorem, ни `your_api_key`, ни пустого TODO без статуса.

Все хиты **LEGITIMATE**:

| Группа | Примеры | Почему не трогаем |
|---|---|---|
| Честное N/A | `KNOWN_BUGS.md` Closed/N/A; sprint2 agreement/nDCG; `offline-deployment`; `dataset-catalog` DEAD_CHANNEL; `samples/xsd/minstroy/SOURCE.md` n/a (no xml:id); CLAIMS_EVIDENCE_MATRIX `n/a` | Нет данных / не применимо, с причиной |
| TBD как история ТЗ v1 | `docs/tz/*`, `TZ_V1_*`, `TZ_COMPLIANCE_MATRIX` «Former TBD», `submission/02-documentation` | Разделы **заполнены** в v2; слово TBD — имя бывшего пробела |
| TBD confirm, не «заполните с нуля» | TIER0, KT3 FAQ, OWNER_ACTIONS OA-8, SAMOLET_QUESTION_PACK, TRACKER SIG-05, KT3_WINDOW | Речь: подтвердить редакцию v2 |
| Customer pack TBD | pilot-claim-boundary, TECHLAB_TASK_07, TZ matrix customer pair | RT-002 OPEN — честный пробел |
| TODO со статусом | `DEFECT_INJECTION_RECALL_PLAN` «код не написан» + имя CLI | Осознанный хвост; не закрывает RT-001 |
| Инвентарь аудита | `AI_TRACE_AUDIT` перечисляет TODO/TBD/N/A как **категории поиска** | Описание скана |

Ложный хит, которого больше нет в регексе: URL `…-na-provedenie…` на `MIK_CRITERION_EVIDENCE_MAP` (слово `na` ≠ `N/A`).

## Гейты после правки

`lint_ai_trace.py` (мета/чат), четыре режима `lint_claims.py`, `check_markdown_links`.  
`lint --full-docs` с `excluded_untracked → 0` — после коммита волны (новые `docs/ai/*` и quality-отчёты ещё не в git).
