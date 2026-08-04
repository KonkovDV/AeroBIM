# Пять операторских состояний проверки — KT#2 / K3

**Дата:** 2026-08-04 (rev 2026-08-04 Red Team wave-2)  
**claim_level:** operator_honesty — не product accuracy  

На поверхности UI и API не смешивать «зелёный отчёт» с «не проверяли».

Историческое имя «четыре состояния» относилось к исходам пакета; **карта покрытия** использует **пять** операторских ярлыков ниже.

## Карта покрытия (файл × семейство) — 5 ярлыков

| Операторский ярлык | `CoverageStatus` | Смысл |
|---|---|---|
| **done** | `checked_ok` | Проверка выполнена; нарушений не найдено |
| **findings** | `checked_findings` | Проверка выполнена; есть находки |
| **not_done** | `not_checked` | Проверка не выполнялась / scope неизвестен |
| **partial** | `insufficient_data` | Запускалась, данных/движка недостаточно |
| **needs_expert** | `requires_expert` | Только advisory — нужен эксперт |

API: `GET /v1/reports/{id}/coverage` → поля `operator_status`, `operator_legend` (schema 1.1.0).  
UI: панель «Карта покрытия проверок».

`done` ≠ `summary.passed` (ADR-001): ярлык семейства на источнике, не вердикт пакета.

## Исход пакета (`PackageOutcome`) — 5 исходов

| Outcome | Операторски |
|---|---|
| `pass` | Нарушений не найдено (проверки прошли Shared-gate) |
| `pass_with_warnings` | Есть предупреждения |
| `review_required` | Требуется эксперт |
| `blocked` | Проверка не завершена / данных недостаточно |
| `failed` | Ошибки или fail-closed |

`summary.passed` = true только для `pass` / `pass_with_warnings` (ADR-001).
