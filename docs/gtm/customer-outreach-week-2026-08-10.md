<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "Customer outreach — week of 2026-08-10"
date: 2026-08-07
status: template
claim_boundary: >-
  Outreach templates only. Checkpoint NO_GO. No invented orgs/emails.
  Placeholders COMPANY_1..COMPANY_5. Fixture-only product claims.
---

# Customer outreach — week of 2026-08-10

**Purpose:** Follow-up templates for five prior contacts, cold-call script for new leads, and Claims Lock wording for live conversations.  
**Tracker schema SSOT:** [`docs/customer/CUSTOMER_OUTREACH_TRACKER_TEMPLATE.csv`](../customer/CUSTOMER_OUTREACH_TRACKER_TEMPLATE.csv)  
**Week instance (example rows):** [`outreach-tracker-week-2026-08-10.csv`](outreach-tracker-week-2026-08-10.csv)

**Rules:** Do not invent real company names, emails, or call outcomes in git. Replace `COMPANY_n` / `[CONTACT_NAME]` / `[OPERATOR_NAME]` before sending. Log verified contacts in private ops (`.local/commercial-ops/`) when live.

Related: [`CUSTOMER_DISCOVERY_SCRIPT.md`](../customer/CUSTOMER_DISCOVERY_SCRIPT.md), [`email-short-ru.md`](../customer-discovery/email-short-ru.md), [`CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md).

---

## 1. Follow-up templates (COMPANY_1 … COMPANY_5)

Use one variant per prior touch. Adjust channel line to match tracker.

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

## 2. Cold call script (new leads)

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

**If «we already use Solibri / Navis»:**

> Тогда полезный разговор — сверка комплекта: чертёж↔модель, модель↔ТЗ, значения↔расчёт. Не сравниваю нас с [vendor] по имени.

**Close:**

> Отправлю одностраничник. Удобнее email или мессенджер?

---

## 3. Claims Lock — say / don't say

| Situation | ✅ Say | ❌ Don't say |
|---|---|---|
| Product accuracy | «На вашем комплекте без эталона не знаю — предлагаем замер с двумя экспертами» | «Точность >90%», «точность AeroBIM», AECV/fixture % as product KPI |
| Demo content | «Покажем открытый регресс и карту покрытия на fixture / open bench» | «Подтверждено на реальных проектах заказчика» (without RT-001 corpus) |
| Expertise role | «Решение о годности документации остаётся за вашим специалистом» | «Система заменяет экспертизу» |
| DWG | «Пилот по умолчанию: IFC + DXF export + PDF; native DWG — вне scope без лицензии» | «Анализируем DWG», «DWG-ready», «поддерживается DWG» |
| MEP | «MEP contour — инженерный scaffold, не delivered clash» | «MEP clash delivered», «полный MEP clash» |
| BCF / CDE | «BCF ZIP structurally OK; импорт в ваш CDE — отдельное доказательство» | «BCF готов к CDE», «CDE-ready», «интеграция с CDE готова» |
| SLA | «Fixture timing — миллисекунды на tiny IFC, не SLA вашего комплекта» | «Комплект ≤30 минут для любого комплекта» |
| Norms | «Draft/template norm packs — advisory only» | «Утверждённый заказчиком нормативный пакет» |
| Checkpoint | «Checkpoint NO_GO до customer evidence по RT-001/002/003» (internal / investor — not cold-call opener) | «Production-ready», «Checkpoint GO» |
| Calculations | «Сверка значений PARTIAL; независимая корректность расчётов не реализована» | «Проверяет корректность расчётов» |
| Open bench | «IFC-Bench / BSI n=290 — регресс, claim_level=open_bench_only» | Open bench % as customer precision |
| Customer interest | Only if verified in tracker | «Заказчики заинтересованы» without logged contact |

Full forbidden list: [`CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md).

---

## 4. Tracker linkage

| File | Role |
|---|---|
| [`CUSTOMER_OUTREACH_TRACKER_TEMPLATE.csv`](../customer/CUSTOMER_OUTREACH_TRACKER_TEMPLATE.csv) | Empty schema SSOT — copy for new weeks |
| [`outreach-tracker-week-2026-08-10.csv`](outreach-tracker-week-2026-08-10.csv) | This week's **example** rows (COMPANY_1..5 placeholders only) |
| [`CUSTOMER_DISCOVERY_SCRIPT.md`](../customer/CUSTOMER_DISCOVERY_SCRIPT.md) | Live call tone reference |
| [`expertise-corpus-scan-2026-08.md`](../datasets/expertise-corpus-scan-2026-08.md) | Data request checklist when `data_available=yes` |

**Weekly ops:** Before Monday standup, owner fills live counts from private log into tracker; do not commit verified personal emails to public git without policy review.

---

## 5. Week goals (honest)

| Metric | Target | Notes |
|---|---|---|
| Follow-ups sent | 5 (COMPANY_1..5) | Templates above |
| New cold touches | ≥10 | Not counted until logged |
| Demos scheduled | ≥1 | Success = slot, not deck sent |
| Pilots agreed | 0 required this week | NO_GO until RT-001 intake |
| NDA initiated | ≥1 if data path opens | Expert-available + data-blocked pattern |
