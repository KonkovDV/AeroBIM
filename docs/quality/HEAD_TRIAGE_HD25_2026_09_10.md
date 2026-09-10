<!-- claims-lint: allow-file reason="HD25 incoming mentor-eve audit vs live git; Checkpoint GO; customer_go false; #40/#41 OPEN; PRs 49/50 merged" -->
---
title: "Триаж HD25 10.09.2026 — входящий аудит накануне показа vs живой git"
status: active
version: "1.0.0"
last_updated: "2026-09-10"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
claim_boundary: >
  Reconciles an incoming audit of main@1c6352cc (then PRs 49 and 50) with
  live AeroBIM git. Checkpoint GO (regulatory_measurement_mvp). customer_go
  false. Not product accuracy. Not customer SLA. Issues #40 and #41 stay
  OPEN. D-05 virtualization exists in code; 1508 is team 31.08 speech, not an
  independent re-run. Test counts live only in runtime-baseline-latest.json.
auditor: "триаж × Red Team"
audited_head: "origin/main d8b62f90 after merge of #49 and #50; incoming slice was 1c6352cc"
---

# Триаж HD25 — входящий аудит накануне показа vs живой git

Метод: входящий текст (срез `main@1c6352cc`, PR #48/#49/#50, D-04…D-12,
FE-DRIFT-01) сверён с деревом после влива #49 и #50. Лексика:
**KILL / HOLD / ACCEPT**. Issues **#40 / #41 / #44** остаются **OPEN**.
`customer_go` **false**.

## 0. Итог

| ID | Verdict | Что |
|---|---|---|
| **HD25-P48-01** | **ACCEPT** | Красный PR #48 не влит. Нужная работа оболочки на `main` коммитом `4c050345` («PR #48 failed tsc on React 19 JSX.Element»). Граница вьюера — класс с `getDerivedStateFromError` / `componentDidCatch`; диагностика `import.meta.env.DEV`. |
| **HD25-D04-01** | **ACCEPT уже в git** | Один `<main id="work-area" tabIndex={-1}>`; skip в `<header>` выше него. WP-FE-34 статус `code`. Не сертификат WCAG. |
| **HD25-P49-01** | **ACCEPT; влито** | 20/20 зелёных на #49. `apiBase` убран из шапки. Сканер `no-debug-artifacts.test.ts`. Merge `94ed7161`. Показ идёт без служебной проводки адреса в презентационный слой. |
| **HD25-P50-01** | **ACCEPT; влито** | FE-DRIFT-01: vitest читает смоук как текст и сверяет `EXPORT_UNSAVED_CONFIRM` со словарём. Merge `d8b62f90`. Сторож усилен: сравнение `message !== EXPORT_UNSAVED_CONFIRM` не должно выродиться в пустые `toContain`. |
| **HD25-CRUFT02-01** | **HOLD** | Нативное `confirm` не трогать накануне показа. Закрытие после показа: диалог + смоук + сторож в одном коммите. Иначе падает OA-21 / #41. |
| **HD25-D05-01** | **KILL входящее «нет виртуализации»** | `VIRTUALIZE_AFTER = 40` уже в `FindingListPanel` (оконный `listbox`, не таблица). Не замерено на 1508. Не объявлять закрытым. `aria-rowcount` — паттерн сетки; здесь follow-on — `aria-setsize` / `aria-posinset` на `role="option"`, не rowcount. |
| **HD25-D08-01** | **HOLD входящее «D-08 открыт»** | D-08 (карта покрытия первой на «Эффект») — code 10.09. D-07 (решение → находка → доказательство) **открыт**. D-06 sticky — partial. D-11/D-12 — open. Речь: бэклог WP-FE-35…38, не «ментор нашёл дыру». |
| **HD25-I40-01** | **HOLD** | #40 и #41 OPEN, живых артефактов в git нет. Не закрывать комментарием. «Полчаса локально» — owner rehearsal (`smoke:decision`, пустое хранилище), не акт закрытия. |
| **HD25-SCAN-01** | **HOLD «обход гейта»** | `docs/quality/` вне **default** `_SCAN_ROOTS` и вне `check_docs_metadata_integrity`. CI `ci.yml` и `frontend-plan` гоняют `--full-docs` — ранбук claims-lint **видит**. Это не сейф. Список «Нельзя» — HDS-SUB-02, не отключение гейта. |
| **HD25-WIN-01** | **KILL; fixed locally** | Сканер #49 сравнивал Windows-пути `features\\shell\\…` с posix-белым списком. CI Linux зелёный, локальный `npm test` на машине показа красный. `rel()` теперь нормализует разделители. |
| **HD25-ID-01** | **ACCEPT путаницу имён** | Сканер в #49 назван `HD24-FE-01`. Документ HD24 — входящий переаудит канала. Не смешивать ID. |

**OVERCLAIM продукта: 0.** Недифференцированное CLOSED: 0.

## 1. Что этот проход делает

1. #49 и #50 влиты в `main` (`d8b62f90`).
2. FE-CRUFT-02 в ранбуке и плане несёт FE-DRIFT-01: не менять окно без смоука.
3. Сторож дубля копирайта проверяет саму сверку, не только имена.
4. Windows-разделители в сканере гигиены (иначе локальный `npm test` красный).
5. Речь HD25 + TIER0.

## 2. Что **не** делать сегодня

- Не заменять `window.confirm` на `<dialog>`.
- Не закрывать #40 / #41 / #44.
- Не виртуализировать «под 1508» в ночь перед показом.
- Не называть D-05 отсутствием виртуализации.
- Не называть покрытие книг ЦНЭ или 1508 точностью продукта.
- Не говорить «фронт сдан». Восемь экранов IA остаются `partial`.

## 3. Речь на показ 11.09

Показ оболочки = review shell, `start.bat` / `python scripts/run_review_shell.py`.
Показ жюри = `python -m aerobim.tools.run_kt3_jury`.
Красная черта — список в [`FRONTEND_MENTOR_DEMO_2026_09_11.md`](FRONTEND_MENTOR_DEMO_2026_09_11.md).
Экспорт: сначала сохранить черновик. BFF = 501. `customer_go` false.

## 4. Финал

Checkpoint **GO** (`regulatory_measurement_mvp`); `customer_go` **false**.
Входящий аудит по #48, D-04, #49/#50 и FE-DRIFT-01 совпадает с git после влива.
Пункт «нет виртуализации» — ошибка среза, не дефект показа. Это не приёмка,
не SLA, не MEP delivered.
