---
title: "Sprint 3 customer outreach pack"
date: 2026-08-07
status: template
claim_boundary: >-
  Templates only — do NOT send messages from this repo. Checkpoint NO_GO.
  Placeholders COMPANY_1..COMPANY_5. No invented orgs/emails/outcomes.
  Fixture-only product claims.
---

# Sprint 3 customer outreach pack (August 2026)

**Purpose:** Follow-up templates for five prior contacts, first-contact script for ~20 new leads, qualification criteria, and Claims Lock wording.  
**Explicit:** This document is **templates only** — operators must not send messages directly from git; replace placeholders and log live contacts in private ops.

**Related:**

- Week instance: [`docs/gtm/customer-outreach-week-2026-08-10.md`](../gtm/customer-outreach-week-2026-08-10.md)
- Tracker schema SSOT: [`docs/customer/CUSTOMER_OUTREACH_TRACKER_TEMPLATE.csv`](../customer/CUSTOMER_OUTREACH_TRACKER_TEMPLATE.csv)
- Data request when `data_available=yes`: [`docs/datasets/customer-data-request-2026-08.md`](../datasets/customer-data-request-2026-08.md)
- Claims Lock: [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md)

**Checkpoint:** **NO_GO** until RT-001 customer corpus + dual adjudication exists.

---

## 1. Follow-up templates (5 of ~20 prior contacts)

Use one variant per prior touch. Replace `COMPANY_n`, `[CONTACT_NAME]`, `[OPERATOR_NAME]` before any live send.

### COMPANY_1 — no reply after intro email

**Subject:** Короткое напоминание — 40 минут локально, без передачи комплекта

```
[CONTACT_NAME], добрый день.

[OPERATOR_NAME], AeroBIM (программа «Техлаб Москва», задача ГК «Самолёт»).
Писал(а) [DATE_CONTACTED] про локальную сверку одного уже проверенного раздела —
файлы остаются у вас, решение о годности документации за вашим специалистом.

Если тема актуальна — удобно ли 40 минут на следующей неделе?
Если нет — ответьте «не сейчас», больше не побеспокою.

[OPERATOR_FULL_NAME]
тел.: [PHONE]
```

### COMPANY_2 — replied «send materials»

**Subject:** Материалы + один вопрос про ваш контур

```
[CONTACT_NAME], спасибо за ответ.

Приложил(а) одностраничник: docs/customer/CUSTOMER_PILOT_ONE_PAGER.md
(или PDF по запросу).

Чтобы не слать лишнее: вам сейчас важнее (а) как система встаёт в ваш
контур on-prem, или (б) что она находит на одном завершённом эталонном разделе?

Если (б) — можем назначить 40 минут: вы загружаете раздел локально, мы
смотрим совпадения/пропуски против вашего эталона. Точность на вашем
комплекте без эталона назвать не могу — это и есть цель пилота.

[OPERATOR_FULL_NAME]
```

### COMPANY_3 — agreed demo, not yet scheduled

**Subject:** Слот на демо — [COMPANY_3]

```
[CONTACT_NAME], добрый день.

Фиксируем демо по AeroBIM для [COMPANY_3]. Предлагаю слоты:
• [OPTION_A]
• [OPTION_B]

Формат: ~40 мин, локально у вас или экран с вашим эталонным разделом.
Покажем открытый регресс + карту покрытия; это не «>90% точности продукта».

Нужен ли NDA до встречи? С нашей стороны готовы подписать до передачи файлов.

[OPERATOR_FULL_NAME]
```

### COMPANY_4 — demo done, pilot not agreed

**Subject:** Следующий шаг после демо — [COMPANY_4]

```
[CONTACT_NAME], спасибо за время на демо [DATE_CONTACTED].

Кратко зафиксировал(а):
• Показали: IDS/IFC регресс на открытых fixture, карту покрытия Exp B.
• Не показывали: точность на вашем комплекте (нет эталонной разметки).

Чтобы перейти к пилотному замеру, нужны:
1) один согласованный раздел + IFC;
2) ваше заключение или внутренний QC-лист (remark pairs);
3) два инженера для независимой разметки TP/FP.

Готов(а) обсудить объём и NDA на 20 минут созвона.

[OPERATOR_FULL_NAME]
```

### COMPANY_5 — expert available, data blocked by NDA

**Subject:** NDA и минимальный комплект для замера — [COMPANY_5]

```
[CONTACT_NAME], добрый день.

Вы отметили, что эксперт ([EXPERT_ROLE]) доступен, но комплект пока нельзя
передавать без NDA — это ожидаемо.

Минимум для старта замера (после NDA):
• один раздел PD/RD + IFC;
• список замечаний с привязкой к листам/элементам;
• два независимых adjudicator для TP/FP.

Можем начать с on-prem: система у вас, файлы не уходят наружу.
Пришлите, пожалуйста, контакт для согласования NDA или шаблон с вашей стороны.

[OPERATOR_FULL_NAME]
```

---

## 2. First-contact script (~20 new leads)

**Opening (30 s):**

> Добрый день, [CONTACT_NAME]. [OPERATOR_NAME], команда AeroBIM — участники «Техлаб Москва», задача по согласованности проектной документации. Не продаю «точность девяносто процентов». Хочу понять, как у вас сегодня сверяют модель, чертежи и ТЗ — вручную или уже есть автоматизация?

**Discovery (listen — do not feature-dump):**

| Question | Why |
|---|---|
| «Как проходит сверка комплекта перед экспертизой или сдачей заказчику?» | Pain mapping |
| «Где чаще расхождения — модель↔чертёж, модель↔ТЗ, расчёт↔модель?» | Scope fit |
| «Есть ли эталонный уже проверенный раздел, с которым можно сравнить без риска для текущего проекта?» | RT-001 path |

**Honest value line:**

> Мы не подменяем эксперта. Показываем совпадения и расхождения против **вашего** эталона. На вашем комплекте без эталона точность назвать не могу — для этого и нужен пилотный замер.

**Ask:**

> Цель звонка — 40 минут on-prem или короткий слот с вашим эталонным разделом, либо имя коллеги, кто планирует такие встречи.

**If «what accuracy?»:**

> На открытых fixture мы публикуем только регресс и synthetic baseline — не product accuracy. На вашем комплекте — только после двух независимых экспертов и согласованной разметки.

**Close:**

> Отправлю одностраничник. Удобнее email или мессенджер?

---

## 3. Qualification questions (Sprint 3)

Ask on first contact or follow-up. Log answers in tracker — do not invent outcomes in git.

| # | Question | Maps to |
|---|---|---|
| Q1 | «В типовом комплекте есть IFC? В какой версии (2x3 / 4 / 4x3)?» | Analyze path; RT-001 intake |
| Q2 | «Чертежи в PDF/A или только DWG?» | DWG-only % risk |
| Q3 | «Есть ли заключение экспертизы или внутренний QC-лист с remark pairs?» | Expertise GT availability |
| Q4 | «Готовы ли передать de-identified pilot pack под NDA (on-prem опция)?» | Data path |
| Q5 | «Какой % разделов уходит заказчику только в DWG без IFC/PDF/A export?» | DWG-only share % |
| Q6 | «Два инженера доступны для независимой разметки TP/FP?» | Dual adjudication |
| Q7 | «MEP federated IFC в scope или только AR/KR slice?» | RT-003 boundary |

---

## 4. Lead qualification criteria

| Tier | Criteria | Next step |
|---|---|---|
| **A — pilot candidate** | IFC + PDF/A available; expertise/QC remark list with anchors; 2 adjudicators; NDA feasible; DWG-only share <50% or export path agreed | Send [`customer-data-request-2026-08.md`](../datasets/customer-data-request-2026-08.md); schedule scope memo |
| **B — nurture** | Interest + partial formats (e.g. PDF only); expert available; data blocked by NDA | NDA template; on-prem demo |
| **C — discovery only** | Pain confirmed; no etalon section; DWG-only >80% | Stay in discovery; no pilot promise |
| **D — disqualify** | No IFC path; no remark list; no adjudicators; expects >90% accuracy claim | Politely close; do not over-promise |

**Hard disqualifiers for RT-001 closure claims:** DWG-only without export; single annotator; no NDA; expects product SLA ≤30 min on any compound.

---

## 5. Contact result fields (tracker schema)

Copy [`CUSTOMER_OUTREACH_TRACKER_TEMPLATE.csv`](../customer/CUSTOMER_OUTREACH_TRACKER_TEMPLATE.csv) for each week. Required columns:

| Column | Values / notes |
|---|---|
| `organization` | Placeholder `COMPANY_n` or verified name (private ops if PII) |
| `segment` | dev / gen_contractor / expertise / design |
| `contact_role` | BIM lead / chief engineer / QC |
| `contact_name` | `[CONTACT_NAME]` until verified |
| `channel` | email / phone / messenger / event |
| `date_contacted` | ISO date |
| `response` | no_reply / interested / not_now / send_materials / demo_agreed / data_blocked |
| `demo_agreed` | yes / no / scheduled |
| `pilot_agreed` | yes / no — expect **no** until RT-001 intake |
| `data_available` | yes / partial / no / nda_blocked |
| `expert_available` | yes / no |
| `NDA_required` | yes / no / in_progress |
| `next_step` | free text |
| `owner` | `[OPERATOR_NAME]` |
| `notes` | DWG-only %, format mix, qualification tier A–D |

**Sprint 3 extension fields (in `notes` or private log):**

- `ifc_present`: yes/no
- `pdf_present`: yes/no
- `expertise_conclusions`: yes/no/partial
- `deid_pack_willing`: yes/no
- `dwg_only_share_pct`: 0–100 estimate

---

## 6. Claims Lock — say / don't say

| Situation | ✅ Say | ❌ Don't say |
|---|---|---|
| Product accuracy | «На вашем комплекте без эталона не знаю — предлагаем замер с двумя экспертами» | «Точность >90%», fixture F1 as product KPI |
| Demo content | «Покажем открытый регресс и карту покрытия на fixture / open bench» | «Подтверждено на реальных проектах заказчика» |
| Expertise role | «Решение о годности документации остаётся за вашим специалистом» | «Система заменяет экспертизу» |
| DWG | «Пилот по умолчанию: IFC + DXF export + PDF/A; native DWG — вне scope, budget licenses = 0» | «Анализируем DWG», «DWG-ready» |
| MEP | «MEP contour — инженерный scaffold, не delivered clash» | «MEP clash delivered» |
| BCF / CDE | «BCF ZIP structurally OK; импорт в ваш CDE — отдельное доказательство» | «BCF готов к CDE», «CDE-ready» |
| SLA | «Fixture timing — не SLA вашего комплекта» | «Комплект ≤30 минут для любого комплекта» |
| LLM | «Regex fixture baseline only; Kimi/Qwen NOT RUN Sprint 3» | «LLM beats regex on customer data» |
| Checkpoint | «Checkpoint NO_GO до customer evidence по RT-001» (internal) | «Production-ready», «Checkpoint GO» |

Full forbidden list: [`CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md).

---

## 7. Sprint 3 outreach targets (honest)

| Metric | Target | Notes |
|---|---|---|
| Follow-ups drafted | 5 (COMPANY_1..5) | Templates §1 — **not sent from repo** |
| New first-contact scripts prepared | ~20 | §2 — log touches in tracker when live |
| Demos scheduled | ≥1 if outreach executed | Success = slot, not deck sent |
| Pilots agreed | 0 required | NO_GO until RT-001 intake |
| Messages sent from git | **0** | Templates only |

---

## 8. Do not send from this repository

- Replace all placeholders before any live communication
- Log verified contacts in private ops (`.local/commercial-ops/`) when policy requires
- Do not commit verified personal emails to public git without policy review
- Do not claim outreach outcomes that are not logged in tracker
