<!-- claims-lint: allow-file reason="Academic literature triage; forbidden phrases as blocked inferences / validity threats; Checkpoint NO_GO" -->
---
title: "Academic literature triage — Kane IUA × AEC 2026 (КТ#2)"
date: "2026-08-16"
status: active
version: "1.0.1"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Adversarial literature map for TechLab/MIK speech. Not a product score.
  Open benches and 2026 agent papers do not close RT-001/002/003.
  Not product accuracy. Not MEP delivered. Not CDE-ready. Not native DWG.
  Harbor NOT_RUN. IDS 1.1 is not a final standard. ISO 19650-6 is H&S sharing, not 5.7 authorization.
---

# Триаж литературы и Red Team валидности (срез 16.08.2026)

**Объект:** IUA freeze [`f9389bf`](https://github.com/KonkovDV/AeroBIM/commit/f9389bf). Шесть столов 17.08 (Gate sell-path, AABB n=6, tracker addendum) не переоткрывают IUA и не закрывают RT-001/002/003.  
**Вопрос:** какие *выводы* из текущих артефактов AeroBIM лицензирует научная картина августа 2026, и какие выводы она прямо запрещает, если их произнести на КТ#2.  
**Метод:** Interpretation/Use Argument (Kane, 2013) поверх шести аспектов Messick (1995), затем атакующее дерево.  
**Checkpoint:** **`NO_GO`**. `closes_rt001: false`. `closes_rt002: false`. `closes_rt003: false`.

Сопровождение: [`RED_TEAM_ACADEMIC_KT2_2026_08_15.md`](RED_TEAM_ACADEMIC_KT2_2026_08_15.md) (рамка IUA) · [`INTERPRETATION_USE_LEDGER_2026_08.md`](INTERPRETATION_USE_LEDGER_2026_08.md) (исполняемый журнал) · [`OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md`](OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md) (L1≠L3).

## 0. Вердикт триажа

Литература 2025–2026 **не открывает** Shortcut к GO. Она сужает разрешённую речь.

| Приоритет | Находка | Следствие для КТ#2 |
|---|---|---|
| **P0** | Hellin et al. (2026) и AEC-Bench (2026) измеряют *извлечение / агентный разбор документов*, не приёмку комплекта ПД+экспертиза | 27/1026 и inventory 196 остаются L1; Harbor **NOT_RUN** |
| **P0** | LLM-as-judge 2026: согласие без κ, смещение позиции, «stakes signaling» | VLM **не** судья TP/FP; dual human raters обязательны |
| **P0** | Clash-management 2026: детекция автоматизирована, фильтрация — нет; большинство хитов не требуют действия | AABB / duplex inventory ≠ MEP delivered |
| **P1** | IDS 1.0 — final (1 June 2024); IDS 1.1 на август 2026 — сбор обратной связи, не стандарт | Аудит `.ids` ≠ checking IFC ≠ EIR Самолёта |
| **P1** | ISO 19650-6:2025 — обмен H&S-информацией, не замена п. 5.7 authorize | Shared-gate ≠ «соответствие ISO 19650» |
| **P2** | Wilson / Brown–Cai–DasGupta остаются корректным планировщиком доли | n=111 — план разметки, не измеренная точность |

**Одна фраза:** внешняя наука 2026 подтверждает, что у нас есть воспроизводимый *контроль* (fail-closed checking) и нет ещё *критериальной валидности* на комплекте назначающей стороны.

Checkpoint stays **NO_GO**.

## 1. Теоретический каркас (что считаем обязывающим)

Валидность — свойство **вывода из оценки к использованию**, не свойство программы (Messick, 1995; Kane, 2013). Воспроизводимость фикстуры закрывает аспекты *content* и *substantive* для движка. Она не закрывает *external/criterion* и *consequential* для решения Техлаба «пилотировать на комплектах Самолёта».

| Источник | Что берём как норму | Что *не* лицензирует |
|---|---|---|
| Messick, S. (1995). *Am. Psychol.* 50(9), 741–749. [doi:10.1037/0003-066X.50.9.741](https://doi.org/10.1037/0003-066X.50.9.741) | Шесть аспектов. Использование балла не по назначению — провал валидности даже при стабильном числе | «Тесты зелёные ⇒ продукт готов» |
| Kane, M. T. (2013). *J. Educ. Meas.* 50(1), 1–73 | IUA обязан назвать *use*. Наш IUA для L1/L2 останавливается на engine regression / open-bench | Критерии пилота 0.60 / 20% экономии / BCF в СОД |
| Cronbach & Meehl (1955). *Psychol. Bull.* 52(4) | Номологическая сеть: well-formedness `.ids` ≠ приёмка Самолёта | 50 IDS / 0 document issues как сертификация |
| Goodhart (1975/1984); Campbell (1979) | Метрика, став целью, перестаёт быть мерой | pytest-count, F1 0.86, 18/22 как KPI пилота |
| Saltzer & Schroeder (1975). *Proc. IEEE* 63(9) | Fail-safe default | Fail-closed = полнота нахождения ошибок |
| Leveson (2011). *Engineering a Safer World* | Безопасность — ограничение управления | `summary.passed` = «можно строить» |
| ISO 19650-2:2018 cl. 5.6–5.7 | 5.6.3 может быть частично автоматизирован; 5.7 — организационный акт | Автопроверка заменяет уполномочивание |
| ISO 19650-6:2025 | Структурированный обмен H&S-рисками в CDE | Мы «закрыли ISO 19650», потому что есть Shared-gate |
| Solihin & Eastman (2015). *Autom. Constr.* 53, 69–82 | Классы 1–4 правил | Шаблон СП 63 covering pset = proof of solution |
| Cohen (1960); Krippendorff (2018) | κ/α требуют ≥2 разметчиков на замороженном пакете | Изобретённый κ |
| Brown, Cai & DasGupta (2001). *Stat. Sci.* 16(2) | Интервал Уилсона для доли лучше Уолда у краёв | n=111 как уже измеренный P/R |
| Teece (1986). *Res. Policy* 15(6) | Appropriability: MIT без юрлица → рента в услугах и размеченном пакете | SKU / SAFE из открытого кода |

## 2. Карта источников августа 2026 (что прочитано)

Ниже — только то, что меняет IUA. Блоги без метода отнесены к **P3** и не используются как критерий.

| ID | Работа | Что измеряет | Лицензированный перенос на AeroBIM | Запрещённый перенос |
|---|---|---|---|---|
| L-AEC | Mankodiya, Gallik, Galanos, Mulyar (2026). AEC-Bench. [arXiv:2603.29199](https://arxiv.org/abs/2603.29199). 196 задач, 9 семейств, Harbor | Агенты на чертежах/спеках/submittals; coding-agents сильны в retrieval, слабы в spatial grounding | Inventory 196; «агентный VLM ещё оценочный фронт»; Harbor **NOT_RUN** у нас | «Мы закрыли AEC-Bench»; overlay = drawing literacy |
| L-IFC | Hellin, Jang, Fuchs, Nousias, Borrmann (2026). BIM information extraction… [arXiv:2605.01698](https://arxiv.org/abs/2605.01698). ifc-bench v2: 1027 QA / 37 IFC / 21 проект | Adaptive exploration vs static query; held-out 514 | Countable **27/1026** smoke; QA ≠ package acceptance; student/open models | Paper F1 / 514 test split как product accuracy; RT-001 CLOSED |
| L-AECV | Kondratenko et al. AECV-Bench. [arXiv:2601.04819](https://arxiv.org/abs/2601.04819) §6 | Raster floor plans, ~120 листов, 4 класса; Door/Window EM низкие | Калибровка: не считать двери/окна на демо | AECV macro как точность AeroBIM |
| L-CLASH | *Buildings* 16(13):2623 (2026). AI in BIM clash management. [doi:10.3390/buildings16132623](https://www.mdpi.com/2075-5309/16/13/2623) | Детекция зрелая; фильтрация/приоритет — человек; majority of hits не требуют действия (Koo; Luo; Lin & Huang) | RT-003 OPEN честен; fixture clearance ≠ coordination issue | «MEP delivered»; duplex AABB 654 = clash delivered |
| L-J1 | *Reliability without Validity* (2026). [arXiv:2606.19544](https://arxiv.org/abs/2606.19544). ~541k judgments, Apr 2026 frontier | Exact-match раздувает согласие на 33–41 п.п. vs Cohen’s κ; position bias сосуществует с test–retest >0.95 | Dual human raters; κ обязателен; LLM-judge не замена L3 | «Модель подтвердила наши findings» |
| L-J2 | *When Judgment Becomes Noise* (2025). [arXiv:2509.20293](https://arxiv.org/abs/2509.20293) | Схемы судей не держатся; ELO маскирует шум | Не строить рейтинг «AI vs эксперт» без психометрики | Сводный балл VLM как критерий пилота |
| L-J3 | *Context Over Content* (2026). [arXiv:2604.15224](https://arxiv.org/abs/2604.15224) | Stakes signaling: судья смягчает вердикт, если знает последствия | Не кормить advisory-модель формулировкой «это решит пилот» | Молчаливый LLM-judge в контуре вердикта |
| L-IDS | buildingSMART IDS 1.0 final 1 June 2024; feedback IDS 1.1 — май 2026, не final | Checking IFC vs audit `.ids` | IfcTester = checking; XmlIdsDocumentAuditor = audit | «IDS certified / профиль Самолёта»; IDS 1.1 как действующий стандарт |
| L-BCF | BCF-API 3.0 + OpenCDE Foundation; Documents API | ZIP ≠ API; Foundation обязателен до BCF-API | Structural ZIP T1; `cde_import=NOT_VERIFIED` | CDE-ready; «BCF виден в СОД» |
| L-19650-6 | ISO 19650-6:2025 (H&S information) | Классификация и обмен рисками; не ISO 31000 | Не заявляем внедрение Part 6 | «Соответствуем всей серии 19650» |
| L-WIL | Frontiers *Psychol.* (2026) 1705653; Brown et al. (2001) | Wilson для биномиальных долей у краёв 0/1 | Планировщик n=111 @ interim 0.60 | Уолд-интервал; n=111 как уже снятый P |
| L-IDS-WF | Dias, Miceli Junior, Pellanda (2026). Requirement-driven BIM verification via IDS. *Autom. Constr.* [doi:10.1016/j.autcon.2026.107043](https://doi.org/10.1016/j.autcon.2026.107043) | IDScribe / cost QTO: IDS as computable information requirements | Analog: IFC+IDS evidence gate is a checking workflow, not a take-off product | «Мы — IDScribe»; cost QTO как Task-07 delivered |
| L-BSI-VS | [buildingSMART IFC Validation Service](https://validate.buildingsmart.org/) | Schema / info takeoff / Gherkin normative layers | Slide anchor: we overlap schema checking locally; map in `evidence/upstream-validate-overlap-2026-08.md` | «Гоняем официальный Validation Service»; шестой конкурент Задачи 07 |

P3 (не критерий): вендорские гайды Navisworks 2026, n8n-воркфлоу VLM, showcase «zero errors on 137 sheets» без протокола разметки.

## 3. Messick × наши баллы (карта подмены конструкта)

Центральный kill-shot тот же, что 15.08: **content/substantive evidence движка продаётся как external/criterion evidence заказчика**. Литература 2026 добавляет три новых подмены.

| Балл в репо | Аспект, который *может* нести | Аспект, если речь срывается | Статус 16.08 |
|---|---|---|---|
| IFC-Bench 27/1026 countable | Content: существуют открытые IFC | Criterion: корпус ПД РФ + экспертиза | **threat** — Hellin сам ставит unit = QA на heterogeneous IFC, не акт экспертизы |
| AEC-Bench inventory 196 | Content: есть workflow-бенч агентов | Generalizability: «мы агентно читаем чертежи Самолёта» | **threat** — Harbor NOT_RUN; авторы: fail on visual grounding |
| AECV live counting | External на *растровых* планах 4 классов | Drawing literacy продукта | **mitigated**, если двери/окна запрещены в демо |
| Fixture F1 ≈ 0.86 | External на **нашей** GT | Product accuracy | **threat** |
| IDS document audit 50/0 | Structural well-formedness | Samolet EIR / IDS 1.1 cert | **threat** |
| IfcClash clearance extra-method | Substantive: режим clearance запускается | MEP coordination delivered | **threat** — *Buildings* 16(13):2623 |
| BCF 2.1 ZIP structural | Substantive T1 | ISO 19650 exchange / OpenCDE | **threat** — Foundation API не доказан на именной СОД |
| `summary.passed=false` fail-closed | Control (Saltzer/Leveson) | Полнота нахождения дефектов | **mitigated**, если речь = «не зеленеем без доказательства» |
| Wilson n=111 | Protocol planning | Уже измеренный 0.60 | **threat** |
| VLM advisory | Content: кандидат для HITL | Судья TP/FP / вердикт | **threat** — 2606.19544, 2604.15224 |

**Consequential validity:** публикация L1/L2 как точности продукта — не «маркетинговый стиль», а неэтичное *использование* балла (Messick). Claims Lock блокирует это использование.

## 4. Отрасль: checking vs intelligence

### 4.1 IDS и EIR

buildingSMART разделяет **IDS checking** (IFC ⊨ IDS) и **IDS audit** (файл спецификации валиден). Final standard — IDS **1.0** (1 June 2024). На май 2026 bSI собирает feedback для 1.1; это **не** утверждённый стандарт. Публичный IDS МОГЭ — требования органа экспертизы, ближе к third-party IR, чем к EIR назначающей стороны (Самолёта). ISO 19650-2 не лицензирует подмену.

Честная фраза: «мы проверяем IFC против явной IDS 1.0 и отказываемся молча пропускать рассинхрон версии схемы».  
Запрещённая: «сертифицированы / профиль Самолёта закрыт / IDS 1.1».

### 4.2 Классы Solihin

Класс 4 (*proof of solution*) по-прежнему **NOT_IMPLEMENTED**. Шаблон покрывающего слоя СП 63 — класс 1 на pset. Литература 2026 по VLM-compliance (гибрид: извлечение → детерминированная проверка) *подтверждает* нашу архитектуру ADR-001 и одновременно запрещает продавать извлечение как проверку нормы.

### 4.3 Clash / MEP

*Buildings* 16(13):2623 (2026): детекция геометрических пересечений индустриально зрелая; управление (filter / prioritize / resolve) остаётся человеческим; эмпирика — высокая доля irrelevant hits (Koo ≈ половина medium/high; Luo >19/20 invalid на трубопроводах; Lin & Huang — pseudo-conflicts). Это прямой запрет фразы «MEP delivered» по факту AABB-инвентаря. RT-003 остаётся OPEN.

### 4.4 BCF / OpenCDE

BCF-API 3.0 требует OpenCDE Foundation. Файловый ZIP — канал миграции/офлайна, не доказательство, что топик *виден* в именной СОД. T2 = log + screenshot + hashes. `cde_import=NOT_VERIFIED`.

### 4.5 ISO 19650-6:2025

Part 6 — цикл H&S-информации (классификация, обмен, не оценка риска по ISO 31000). Не реализован. Упоминание «ISO 19650» без номера части — underrepresentation: у нас есть технический Shared-gate (5.6.3-подобный контроль), нет организационного 5.7 и нет Part 6.

## 5. Измерение: почему RT-001 — не задача поиска датасета

Протокол пилота уже регистрирует интервал Уилсона, двух разметчиков и κ/α. До замороженного пакета с двумя именами:

- P/R **не определены**, а не «низкие»;
- κ/α не вычислимы;
- единица анализа (finding / лист / раздел / проект) не согласована с заказчиком.

Hellin (2026) явно расширяет ifc-bench открытыми вопросами *суждения и оценки* — это другой конструкт, чем «замечание экспертизы на ПД РФ». AEC-Bench оценивает агентный workflow на публичных стройкомплектах США/публичного сектора, не на российской экспертизе. AECV §6 сам ограничивает корпус.

Планировщик n=111 для interim 0.60 при ожидаемом 0.75 — *precision-based sample size* (Bland 2009; Brown et al. 2001), не результат. Frontiers 2026 подтверждает Wilson для AI-scoring у краёв 0/1. Уолд на малых n запрещён в речи.

## 6. LLM-as-judge: почему advisory не становится арбитром

Три независимых линии 2025–2026:

1. **Надёжность без валидности** (2606.19544): exact-match раздувает согласие; κ обязателен; высокий test–retest совместим с тяжёлым position bias.  
2. **Шум схемы** (2509.20293): судья не держит заявленную рубрику; агрегации создают иллюзию порядка.  
3. **Stakes signaling** (2604.15224): сообщение о последствиях вердикта смещает судью *без* следа в chain-of-thought.

Следствие для AeroBIM: VLM остаётся источником *кандидатов*. TP/FP на пилоте ставят два человека. Модель не ставит `summary.passed` (ADR-001). Кормить модель текстом «от этого зависит пилот 2 млн ₽» — отдельная угроза смещения, даже если вердикт формально за движком.

## 7. Дерево атак (продолжение RT-ACAD)

Нумерация продолжает [`RED_TEAM_ACADEMIC_KT2_2026_08_15.md`](RED_TEAM_ACADEMIC_KT2_2026_08_15.md).

| ID | Угроза (Messick/Kane) | Экспонат 2026 | Тормоз |
|---|---|---|---|
| RT-ACAD-17 | Подмена: IFC-Bench QA → акт экспертизы | Hellin 2605.01698; 27/1026 smoke | `claim_level=open_bench_only`; RT-001 OPEN |
| RT-ACAD-18 | Подмена: inventory AEC-Bench → «агент читает ПД» | 2603.29199; Harbor NOT_RUN | Не называть NOT_RUN как прогон |
| RT-ACAD-19 | VLM-as-judge вместо dual raters | 2606.19544 κ-deflation; 2509.20293 | PrecisionClaim.publishable only |
| RT-ACAD-20 | Stakes signaling на advisory-контуре | 2604.15224 | Не формулировать «пилот зависит от модели» в prompt |
| RT-ACAD-21 | Геометрический хит → coordination issue | *Buildings* 16(13):2623 | `mep_system_clash=NOT_VERIFIED` |
| RT-ACAD-22 | IDS 1.1 / «certified» | bSI feedback май 2026, не final | Только IDS 1.0 checking + audit split |
| RT-ACAD-23 | «Соответствуем ISO 19650» без части | 19650-6:2025 = H&S; 5.7 = человек | ADR-001; не Part 6 |
| RT-ACAD-24 | n=111 как измеренный 0.60 | Wilson planner ≠ score | protocol_planning only |
| RT-ACAD-25 | ZIP BCF → OpenCDE Foundation + именная СОД | BCF-API 3.0 requires Foundation | T2 checklist empty |

## 8. Что этот проход *не* делает

Не запускает Harbor. Не размечает корпус Самолёта. Не закрывает RT-001/002/003. Не добавляет класс 4 solver. Не внедряет ISO 19650-6. Не делает IDS 1.1 стандартом. Не переписывает историю git.

Человеческие условия GO (юрлицо, LOI, пакет + два разметчика, именная СОД) кодом не создаются. Видео не записываем. Сочинить их — consequential-validity failure.

## 9. Речь на КТ#2, которую литература *разрешает*

> У нас fail-closed слой проверки IFC-комплекта: требование, объект, доказательство, отказ молчать при срыве проверки. Открытые бенчмарки 2026 калибруют ожидания агентов и извлечения; они не заменяют размеченный комплект назначающей стороны. Поэтому checkpoint **NO_GO**, пока нет корпуса, профиля и измеренного federated MEP.

Формула прежняя: не больше функций → ужеже scope → реальный пакет → измеренный эффект → затем интеграция.

Checkpoint stays **NO_GO**.
