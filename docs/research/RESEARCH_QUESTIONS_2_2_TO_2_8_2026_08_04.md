---
title: "Research questions 2.2–2.8 — multi-source verified summary"
date: 2026-08-04
status: active
version: "1.0.0"
claim_boundary: >-
  Literature and law map only. Checkpoint remains NO_GO.
  Foreign / vendor numbers are not AeroBIM product KPIs.
  Does not close RT-001/002/003. claim_level=research_only.
---

# Вопросы 2.2–2.8 — сверенный свод

Дополнение к [`AECV_BASELINE_COMPARE_2_1_2026_08_04.md`](AECV_BASELINE_COMPARE_2_1_2026_08_04.md) (вопрос 2.1 уже закрыт: four-field **0.507**) и к [`SOURCE_VERIFICATION_REPORT_2026_08_04.md`](SOURCE_VERIFICATION_REPORT_2026_08_04.md).

**Протокол:** audit → gap-fill → статус `VERIFIED` / `PARTIAL` / `UNVERIFIED` / `VENDOR` / `FABRICATED`.  
**C.3** в конце обязателен.

---

## Статусная таблица

| # | Вопрос | Вердикт для слайдов | Сильнейший якорь |
|---|---|---|---|
| 2.2 | Разрешение / качество VLM | **PARTIAL** | Qwen2-VL Table 7 + AeroBIM token matrix |
| 2.3 | LLM→IDS с числами | **VERIFIED** (peer) | Perov ICDMW DOI + abstract numbers |
| 2.4 | Протоколы оценки | **PARTIAL** | AECV hybrid; ChartMuseum $0.2 judge cost |
| 2.5 | Инъекция через документ/изображение | **PARTIAL** | MPI 4D taxonomy; CSA ASR peak 64%; no silver bullet |
| 2.6 | ПДн на чертежах / облако | **PARTIAL** | RKN 140 + ПП 1154; stamp crop = product necessity |
| 2.7 | Регуляторный контур РФ | **PARTIAL→уточнён** | 309-ФЗ (kremlin) ≠ блоговая «часть 16 = УКЭП» |
| 2.8 | Реальные внедрения с метриками | **PARTIAL / VENDOR split** | MDPI HITL 90% effort; vendor ACC/Optellix/AI-BOB |

---

## 2.2 — Разрешение и качество (стоимость vs читаемость)

### Что измерено у нас (ops, **VERIFIED** in-repo)

| Вход | `prompt_tokens` (vision) |
|---|---:|
| Нативный ~522 KB лист | **2184** |
| long-side 1024 / 512 / 256 | **1065 / 297 / 105** |
| completion (thinking off) | ≈**47** |

Токены растут примерно квадратично с линейным размером — согласуется с dynamic tiling VLMs.

### Литература (**VERIFIED** primary PDF / arXiv)

**Qwen2-VL** arXiv:2409.12191, Table 7 (Qwen2-VL-7B):

| Strategy | Avg image tokens | InfoVQA | OCRBench |
|---|---:|---:|---:|
| Fixed 64 | 64 | 28.85 | 572 |
| Fixed 576 | 576 | 65.72 | 828 |
| Fixed 1600 | 1600 | 74.99 | 824 |
| Fixed 3136 | 3136 | **77.27** | 786 |
| Dynamic | **1924** | 75.89 | **866** |

Вывод авторов: нет одного оптимального fixed resolution; dynamic близок к лучшим при меньшем среднем числе токенов. Fig.4: рост `min_pixels` в разумных пределах улучшает InfoVQA / OCRBench / HallusionBench; чрезмерный апскейл мелких картинок может увести в OOD.

**Qwen2.5-VL** tech report / HF: пользователи задают `min_pixels` / `max_pixels` (типичный рабочий диапазон токенов 256–1280 для баланса).

### Не найдено (**UNVERIFIED**)

Пиксельный «минимум читаемости штампа АР» на AEC title blocks в peer literature. Следующий engineering шаг: stamp-crop matrix 512/1024 на живой модели (не выдумывать N px из воздуха).

### Следствие для AeroBIM

- Экономика гранта: crop + long-side cap — обоснованы и литературой, и замером.
- Не утверждать «штамп читается с N px» без своего эксперимента.

---

## 2.3 — Конвейеры LLM→IDS с числами

### Perov et al. (**VERIFIED** Crossref + IEEE abstract)

| Поле | Значение |
|---|---|
| Title | *From Regulations to IDS: A Tool-Augmented LLM Pipeline for Automated BIM Rule Checks* |
| Venue | 2025 IEEE ICDMW, pp. 1696–1702 |
| DOI | `10.1109/icdmw69685.2025.00203` |
| Affiliation | ITMO University, St. Petersburg |

**Числа из abstract (IEEE / DOI landing synthesis):**

| Метрика | С repair loop | Без repair |
|---|---:|---:|
| XML-valid | **100 %** | 62.8 % |
| XSD-valid | **94.1 %** | 59.6 % |
| Solibri-executable | **77.5 %** | — |
| Экспертный набор | **138** requirements | |

Семантика: все структурно валидные выходы заявлены семантически корректными на 77.5 % покрытия датасета; остаток — онтологическое выравнивание IFC.

**Полный PDF IEEE** в этой сессии **не** открыт (robot / timeout) → точные таблицы ablation помечать `PARTIAL` до PDF; abstract numbers можно цитировать с DOI.

### Соседние линии (**PARTIAL**, ids only / prior)

| Работа | ID | Заметка |
|---|---|---|
| Ishigaki-IDS | arXiv:2606.08545 | verifier-aware open weights |
| Ishigaki-IDS-Bench | arXiv:2605.22079 | expert pass rates hard |
| P4IR | arXiv:2606.22402 | RL vs rule hallucination |
| Li (TUM) agent ACC | mediaTUM 1840853 | F1 **0.976** claimed — thesis, re-open before deck |
| BuildThemis | AEI `10.1016/j.aei.2025.103676` | code compliance LLM; **not** AECV |

### Следствие

TZ: «advisory компилятор + HITL; метрики сопоставляем с Perov/Ishigaki» — **allowed**.  
«Первый / SOTA / без аналогов» — **forbidden**.  
Российский СП/ГОСТ end-to-end published compiler: **не найден** → честный gap для RT-002.

См. [`LLM_TO_IDS_BASELINE_2026_08_03.md`](LLM_TO_IDS_BASELINE_2026_08_03.md).

---

## 2.4 — Протоколы оценки (hybrid vs dual labeling)

### AECV-Bench (**VERIFIED** PDF already)

- Counting: exact-match + MAPE (автомат).
- QA: automatic match + LLM-as-a-judge + human adjudication на спорных.

### ChartMuseum (**VERIFIED** arXiv:2505.13444 / NeurIPS DB track PDF)

| Claim | Number | Status |
|---|---|---|
| Human accuracy (100-sample subset) | **93 %** | VERIFIED paper |
| Judge model | `gpt-4.1-mini-2025-04-14` | VERIFIED |
| Cost to judge full benchmark | **~$0.20** | VERIFIED paper |
| Best proprietary (paper era) | Gemini-2.5-Pro **63 %** | VERIFIED |
| Best open (paper era) | Qwen2.5-VL-72B **38.5 %** | VERIFIED |

Это **не** AEC object counting и **не** κ dual-expert. Показывает только: LLM-judge дёшев как triage; human ceiling далеко.

### Не найдено (**UNVERIFIED**)

Head-to-head AEC counting: hybrid (auto+LLM+human) vs dual-expert Cohen κ + cost ratio.  
Запрещено: «в 4 раза дешевле dual labeling» без VERIFIED study.

### Следствие для WP-07 / RT-001

Wilson + dual expert на customer corpus остаётся золотым стандартом. LLM-judge — triage only (Claims Lock).

---

## 2.5 — Инъекция через документ / изображение

### Каркас угроз (**PARTIAL→VERIFIED taxonomy**)

**QPAIN / IEEE 2026** *Multimodal Prompt Injection: A Formal 4D Taxonomy* DOI `10.1109/qpain69676.2026.11545895` (Crossref-class venue):

- \(\mathcal{T}=\langle C,L,O,S\rangle\) — carrier, pipeline location, objective, stealth → до **96** классов; авторы: ~**7.3 %** documented; **no singular defense** covers all; deployable defenses ≤**~75 %** dimensional coverage.

### Измеренные ASR / защиты (**PARTIAL** — secondary + CSA note)

| Claim | Source class | Number |
|---|---|---|
| Typographic IPI peak ASR (stealth) vs GPT-4V/Claude/Gemini/LLaVA | CSA research note 2026 (cites IPI Mar 2026) | **64 %** black-box peak |
| Layered sanitization reduces attack effectiveness | Secondary blog summarizing 2025 stego study | ~**¾** — treat as **PARTIAL** until primary opened |
| ARGUS (CVPR 2026) steering defense | OpenAccess CVPR abstract | qualitative robust IPI defense; **no** single % for AeroBIM slides |

### Следствие для продукта

Оставить: fail-closed HybridRouteGate, stamp crop, no tool fire from untrusted drawing OCR as instruction.  
Не цитировать выдуманные ASR «наша защита = X%».  
Рисовать threat model 4D на Red Team — **да**.

---

## 2.6 — ПДн на чертежах / облако / обезличивание

### Нормативка обезличивания (**VERIFIED** secondary + Garant methods excerpt)

| Акт | Что |
|---|---|
| Приказ Роскомнадзора **19.06.2025 № 140** | Требования и методы обезличивания (идентификаторы, семантика, перемешивание, декомпозиция, преобразование) |
| ПП РФ **01.08.2025 № 1154** | Требования / методы / Правила обезличивания |
| Вступление методов (industry wiki) | с **01.09.2025** |

Denuo / privacy-advocates (opened): раздельное хранение исходных и обезличенных; даже переданные государству обезличенные ПД остаются в режиме 152-ФЗ п.9.1 ст.6.

### Чертежи (**PARTIAL**)

- ФИО / организация в штампе — типичная практика титульных блоков (ГОСТ 2.104-класс); **не** открывали текст ГОСТ как primary в этом pass.
- Судебных прецедентов «PDF АР в облачном VLM = нарушение 152-ФЗ» **не** найдено → не выдумывать.
- Product necessity: **stamp-region crop / redact** перед внешним vision API — инженерная и compliance-гигиена, не «утверждённый метод РКН для чертежей».

### Следствие

На слайдах: «минимизация ПДн до отправки в LLM» + ссылка на 140/1154 как общий контур.  
Не: «РКН одобрил наш crop».

---

## 2.7 — Регуляторный контур РФ (углубление)

### Уже VERIFIED ранее

| Тема | Статус |
|---|---|
| ПП **331** ТИМ | VERIFIED (Garant) |
| **243-ФЗ** (ИИ) | VERIFIED existence on pravo; ≠ March draft labeling |
| Реестр ПО + foreign open weights on Yandex Studio | **PARTIAL** — counsel before «sovereign AI» |

### 309-ФЗ и УКЭП — **критическое уточнение (C.3)**

**VERIFIED primary:** [kremlin.ru/acts/bank/52239](http://kremlin.ru/acts/bank/52239) — ФЗ от 31.07.2025 № **309-ФЗ** «О внесении изменений в ГрК РФ», сила с **1 марта 2026**.

Что реально делает ст.1 п.6 (дополнение ст. **55.5-1** частями 15–16) по текстам kremlin / Kontur:

- ч.15 — уведомление НО СРО о прекращении трудовых отношений специалистом;
- ч.16 — **информирование** НО СРО органами экспертизы / надзора о специалистах, по результатам которых выданы **отрицательные** заключения / отказы ЗОС.

Это **не** формулировка «с 1 марта все листы ПД подписываются УКЭП».

**УКЭП vs ИУЛ (**PARTIAL→VERIFIED** secondary official letter):**

| Источник | Статус | Содержание |
|---|---|---|
| Письмо Минстроя **30.01.2026 № 4420-КМ/14** | **VERIFIED** existence (Consultant / Garant annotation) | ИУЛ **не** заменяет УКЭП; ПД без УКЭП ответственных **не** электронный документ для экспертизы |
| Блоги «309-ФЗ ч.16 = УКЭП» | **OVERCLAIM** | Смешивают дату силы 309-ФЗ с отдельным разъяснением Минстроя + 63-ФЗ |

**Корректная формулировка для КТ:**

> С 01.03.2026 усиливается персональная ответственность ГИП/специалистов (309-ФЗ). Параллельно Минстрой (письмо 4420-КМ/14) фиксирует: на экспертизу — **УКЭП**, не ИУЛ. Основание подписи — **63-ФЗ** + правила электронной ПД, а не «ч.16 55.5-1 про УКЭП».

### ЕСИМ

По-прежнему **PARTIAL** (industry articles only) — не ставить жёсткие даты на слайд без official text.

---

## 2.8 — Промышленные внедрения с измеренными результатами

### Peer / journal (**VERIFIED** DOI / abstract)

| Source | Metric | Caveat |
|---|---|---|
| MDPI *Buildings* 2026, DOI `10.3390/buildings16040719` HITL rule generation (State Grid) | Translation **95.8 %**; executability **98.3 %**; effort **168 h vs 1620 h (−90 %)**; change processing **−94 %** | Chinese power infra; English transfer **79.2 %** F1 — не РФ ПД |
| Editorum / INFRA-M article (naukaru) residential 5240 m² | Check 285 reqs in **22 min**; labor **344→96 h (−72.1 %)**; +**29.3 %** findings vs manual | Russian journal; open full methods before investor KPI copy |

### Program / vendor (**VENDOR** unless audited)

| Claim | Source | Label |
|---|---|---|
| −45 % design review turnaround; −85 % backlog (SEVEN / ACC) | IJIRMPS DOI `10.37082/ijirmps.v13.i3.232468` | **PARTIAL** (trade journal / low citation) |
| 85 % faster rule checks (Symfoni / Optellix) | Vendor case study | **VENDOR** |
| «days → minutes» (AI-BOB / Opper) | Vendor story | **VENDOR** |
| Structured AI «400+ issues / 1000 pages» | Company blog | **VENDOR** (fundraise VERIFIED separately) |

### Следствие

На органайзерские слайды — только peer HITL / AECV open-bench.  
Конкурентов с vendor % — не называть как «доказанная точность рынка».

---

## Часть C — сводка для Claims Lock

### C.1 Что можно говорить

1. Four-field AECV live **0.507** ≈ Gemini paper **0.51** (после B.5) — open bench only.
2. Perov: repair loop поднимает XML/XSD validity с ~60 % до 100 %/94 %; Solibri-exec **77.5 %** на 138 reqs.
3. VLM: resolution↑ → OCR/InfoVQA↑ до насыщения; токены ≈ квадратичны (свой замер + Qwen2-VL).
4. MPI: формальная таксономия; одной защиты нет; stamp crop + fail-closed — разумный минимум.
5. ПДн: 140/1154 — общий контур обезличивания; crop штампа — практика минимизации.
6. 01.03.2026: 309-ФЗ (ответственность/уведомления) **+** позиция Минстроя по УКЭП/ИУЛ — **раздельные** якоря.

### C.2 Что подтверждает текущий продукт

- Advisory LLM + deterministic sign-off.
- `open_bench_only` / RT-001 OPEN.
- Нет уникальности LLM→IDS.
- Экономика vision crop.

### C.3 Что противоречит / ломает черновики (**обязательно**)

1. **Блоги «309-ФЗ ч.16 = обязательная УКЭП»** противоречат тексту 309-ФЗ на kremlin: ч.16 — уведомление НО СРО о негативных заключениях. Исправлять цитирование до КТ#3.
2. **Пять полей 0.43 vs paper 0.51** без оговорки Space — уже зафиксировано в 2.1; не повторять.
3. **«Sovereign Qwen on Yandex = реестр РФ»** — по-прежнему OVERCLAIM (PARTIAL law).
4. **Vendor 85 %/days-to-minutes** рядом с peer 0.51 AECV — смешивает категории доказательств.
5. **«Минимум N px для штампа из литературы»** — всё ещё **UNVERIFIED**; только свой замер.

---

## Limits

- Checkpoint **NO_GO**.
- Не поднимать product accuracy.
- Не коммитить секреты / ключи.
- Полный PDF Perov и полный текст письма 4420 — желательны до investor legal memo.
