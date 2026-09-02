<!-- claims-lint: allow-file reason="Academic lit radar; third-party F1/mandate figures as their claims; not AeroBIM accuracy; NO_GO" -->
---
title: "Academic Literature Review & World-Practice Radar — September 2026"
status: active
version: "1.1.4"
last_updated: "2026-09-02"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Working radar. Web-checked 2026-09-02. Not product accuracy. Not partner hours.
  Third-party volumes and F1 stay theirs. Checkpoint NO_GO; RT-001/002/003 OPEN.
---

# Академический обзор: related-work, мировые практики, кейсы — сентябрь 2026

Jury/preprint extract (tracked): [`../RELATED_WORK_PREPRINT_2026_09.md`](../RELATED_WORK_PREPRINT_2026_09.md).
Этот файл — рабочий радар с журналом сверки. Не закрывает RT.

**Сверка веба:** 02.09.2026. Непроверенное — `UNVERIFIED`. Счётчики цитирований из черновика («×29», «×71», «×6») **сняты**: живой Scholar/Crossref на эту дату их не подтвердил.

## 0. Журнал сверки (матрица «9 позиций»)

| ID | Статус | Что поправили |
|---|---|---|
| Iversen & Huang | VERIFIED | Заголовок *Leveraging large language models for BIM-based automated compliance checking*; AuC **182** (Feb 2026) art. **106707**; DOI `10.1016/j.autcon.2025.106707` (online 05.12.2025); PII `S0926580525007472`. DSR, LLM как reasoning engine. Их F1 на интерпретации/исполнении — **их** eval, не AeroBIM. |
| Fuchs et al. | VERIFIED | Не тезис. EC3 2026 (Jul), Konferenzbeitrag: *Assessing the Viability of LLM Agents for Generating Reusable Compliance Checking Functions* (Fuchs, Hellin, Borrmann). [mediaTUM 1854862](https://mediatum.ub.tum.de/node?id=1854862). |
| Xiao et al. | VERIFIED | *Automating geometry-intensive compliance checking in BIM…*; AuC **189** art. **107038**; DOI `10.1016/j.autcon.2026.107038`; e-pub 02.06.2026. PII `S0926580526002797`. SGR-BIM; пожарные нормы. Их цифры — их eval. |
| Zentgraf et al. | VERIFIED | *A BIM-based framework for automated building code extraction and compliance checking*; AEI **74** 104735; DOI `10.1016/j.aei.2026.104735`; published 11.05.2026. STS/ISOProps → SHACL. |
| Madireddy et al. | VERIFIED | *Large Language Model-Driven Code Compliance Checking in Building Information Modeling*; Electronics **14**(11) 2146; DOI `10.3390/electronics14112146`. LLM пишет Python под **Revit**, HITL. |
| Springer ML 2026 | VERIFIED, **не BIM** | Simbola et al., *LLM-Driven Compliance Checking for Natural-Language Policies over Data Product Descriptors*; Mach Learn **115**, 116 (2026); DOI `10.1007/s10994-026-07038-6`. YAML-дескрипторы data products, не строительные нормы. |
| Ishigaki-IDS-Bench | VERIFIED | arXiv:[2605.22079](https://arxiv.org/abs/2605.22079). 166 gold IDS. AeroBIM smoke: **EXECUTED** 166/166 processability gold XML (`claim_level=open_bench_only`), **не** generation F1 авторов. Не SKIPPED. |
| BIM-Edit | VERIFIED | arXiv:[2606.20146](https://arxiv.org/abs/2606.20146). NL-edit IFC, не проверка комплекта. |
| Cheung et al. | VERIFIED | *Institutionalizing automated compliance checking (ACC)…*; BRI; DOI `10.1080/09613218.2026.2686293`; e-pub 21.06.2026. Evidence–engine alignment как условие explainability. |
| Dias, Miceli Junior, Pellanda | VERIFIED 02.09 Crossref | *Information requirement-driven BIM verification for construction cost estimation… IDS*; AuC **189** art. **107043**; DOI `10.1016/j.autcon.2026.107043`. QTO/cost, не pack ACC. |
| Perov, Filatova, Timoschak, Nasonov | VERIFIED 02.09 Crossref | *From Regulations to IDS: A Tool-Augmented LLM Pipeline for Automated BIM Rule Checks*; ICDMW 2025 pp. 1696–1702; DOI `10.1109/icdmw69685.2025.00203`. Не склеивать с *Buildings* 15 art. 2927. |
| Wang, Hwang, Han, Gupta | VERIFIED 02.09 Crossref | *Generative AI-Assisted Compliance Checking for Construction Requirements*; J. Constr. Eng. Manage. **152**(8) art. 04026117; DOI `10.1061/jcemd4.coeng-18122`. |
| Zhang et al. (Buildings HITL) | VERIFIED 02.09 Crossref | *Human-in-the-Loop Semantic Rule Base Generation…*; Buildings **16**(4) 719; DOI `10.3390/buildings16040719`. Их 95.8 % / −90 % часов — **их** eval, не AeroBIM. |
| SNOWTEC (Hettiarachchi et al.) | VERIFIED 02.09 Crossref | *SNOWTEC: Synthetic Natural language Oversampling…*; MLWA **24** art. **100911** (июнь 2026); DOI `10.1016/j.mlwa.2026.100911`. |

**Новые строки (≤6 мес, VERIFIED Crossref 02.09.2026):** Dias AuC 107043; Perov ICDMW; Wang JCEM; Zhang et al. Buildings 16(4) 719; SNOWTEC MLWA 100911; Ishigaki-IDS модель arXiv:[2606.08545](https://arxiv.org/abs/2606.08545). Не закрывают окна новизны. Журнал ссылок: [`LINK_FACTCHECK_2026_09.md`](LINK_FACTCHECK_2026_09.md).

## 1. Related-work матрица (для preprint)

| Работа | Место/год | Метод | Отношение к AeroBIM | Угроза новизне | Действие |
|---|---|---|---|---|---|
| [Iversen & Huang](https://www.sciencedirect.com/science/article/pii/S0926580525007472) | AuC 182 (2026) 106707 | DSR; LLM интерпретирует норму, выбирает tool, исполняет, пишет отчёт | Ближайший prior art. У них LLM **на маршруте** проверки. У AeroBIM LLM вне `summary.passed` (ADR-001) | Средняя: пересечение «LLM + функции» | Главный контраст. Их F1 не переносить |
| [Fuchs, Hellin, Borrmann](https://mediatum.ub.tum.de/doc/1854862) | EC3 Jul 2026 | Code-Act агенты **генерируют** reusable checking-функции; IDS-validated требования | Prior art для narrative-synthesizer / IDS-compile. У AeroBIM pack с `rule_pack_hash` / `approval_ref` | Средняя | Цитировать; reproducibility vs генеративность |
| [Perov et al.](https://doi.org/10.1109/icdmw69685.2025.00203) | ICDMW 2025, 1696–1702 | Tool-augmented LLM: регламент → IDS | Рядом с Fuchs: генерация IDS, не Shared-gate. Не склеивать с *Buildings* 15:2927 | Средняя | Черновик IDS; `approval_ref` pack |
| [Dias, Miceli Junior, Pellanda](https://doi.org/10.1016/j.autcon.2026.107043) | AuC 189 (2026) 107043 | IDS как information requirements → проверка модели для **сметы/QTO** | Analog openBIM/IDS, не IDScribe и не cost take-off как продукт | Низкая | Цитировать как IR-driven verification, не наш sell-path |
| [Wang, Hwang, Han, Gupta](https://doi.org/10.1061/jcemd4.coeng-18122) | JCEM 152(8) 2026 | Generative AI-assisted compliance checking | LLM на маршруте требований. У нас advisory-only (ADR-001) | Средняя | Контраст вердикта; их метрики не переносить |
| [Zhang et al.](https://doi.org/10.3390/buildings16040719) | Buildings 16(4) 719 (фев 2026) | HITL + BERT/CFG → semantic rule base / KG | Близко к HITL-контуру; генерация правил, не `summary.passed` | Низкая | Их 95.8 % не наша цифра |
| [Xiao, Koh, Ma, Cheng](https://doi.org/10.1016/j.autcon.2026.107038) | AuC 189 (2026) 107038 | Граф (SGR-BIM) для geometry-intensive CC, пожарные нормы | Поле закрывает геометрию, которую AeroBIM держит в `NOT_VERIFIED` (RT-003) | Низкая | Дорожная карта geometry-волны, не поставка |
| [Zentgraf, Hagedorn, König](https://doi.org/10.1016/j.aei.2026.104735) | AEI 74C 104735 (май 2026) | Smart Standard STS + ISOProps → SHACL на IFC | Пересекается с извлечением требований / формализацией | Низкая | Уже в `docs.md`; DOI живой |
| [Madireddy et al.](https://doi.org/10.3390/electronics14112146) | Electronics 14(11) 2146 (2025) | LLM пишет скрипты под Revit + HITL | LLM-in-the-loop, native CAD. AeroBIM — IFC-first, native fail-closed | Низкая | Тренд; не native DWG/RVT delivered |
| [Simbola et al.](https://doi.org/10.1007/s10994-026-07038-6) | Mach Learn 115:116 (2026) | LLM-CC над NL-политиками **data products** | Смежный (не BIM/IFC/IDS) | Нет | Обзор тренда LLM-compliance, не prior art ACC |
| [Ishigaki-IDS-Bench](https://arxiv.org/abs/2605.22079) | arXiv 2026 | Бенчмарк **генерации** IDS XML (166) | Evidence-контур: processability gold IDS. Не F1 генерации как точность продукта | — | Держать `open_bench_only` |
| [Ishigaki-IDS](https://arxiv.org/abs/2606.08545) | arXiv Jun 2026 | Verifier-aware модель черновика IDS | Смежный IDS-compile; не Shared-gate | Низкая | Цитировать рядом с бенчем |
| [BIM-Edit](https://arxiv.org/abs/2606.20146) | arXiv Jun 2026 | NL-редактирование IFC | Смежный (правка модели, не проверка комплекта) | Низкая | Цитировать как соседний бенч |
| [Cheung et al.](https://doi.org/10.1080/09613218.2026.2686293) | BRI, e-pub Jun 2026 | Институционализация ACC в Европе; evidence–engine alignment | Рамка для выводов: provenance как governance. Не закрывает machine-readable finding-контракт | — | Введение / discussion |
| [SNOWTEC](https://doi.org/10.1016/j.mlwa.2026.100911) | MLWA 24 (июнь 2026) 100911 | Transformer IE из норм → KG (Hettiarachchi et al.) | Смежный extraction, не вердикт | Нет | Обзор IE |

### Формулируемый вклад (draft)

Не произносить жюри слово «первый в мире». Черновик для preprint (EN ниже). После adjudication n≥30 на независимом корпусе заменить «доказуема на уровне кода» на «доказуема на уровне кода **и** измерена на названном корпусе (Wilson CI)».

**RU:** open-source acceptance gate для IFC-комплекта, в котором (а) нейтральность вердикта к LLM доказуема кодом (писатели ERROR + DeterminismGate + тесты; ADR-001), (б) каждое замечание — доказательный объект (provenance / expected / observed / evidence-refs + claim-метка), (в) fail-closed распространён на дрейф форматов внешних движков (SKIPPED→ERROR, статус-энумы, ε-гарды), (г) воспроизводимость — reproducibility-hash с origin-фильтром advisory. Это **не** точность на комплекте Самолёта и **не** закрытие RT-001/002/003.

**EN (preprint skeleton):** We describe an open-source IFC-pack acceptance gate in which (i) LLM/VLM outputs are excluded from `summary.passed` by construction, (ii) each finding is an evidence object, (iii) external engine format drift fail-closes rather than silently passing, and (iv) advisory traces are origin-filtered under a reproducibility hash. Partner-pack accuracy remains unmeasured (`NO_GO`).

### Три тезиса для жюри (с цитатами)

1. **Контраст вердикта.** Поле 2026 ставит LLM на маршрут проверки ([Iversen & Huang, AuC 182](https://www.sciencedirect.com/science/article/pii/S0926580525007472) — интерпретация → выбор tool → исполнение → отчёт; [Fuchs et al., EC3](https://mediatum.ub.tum.de/doc/1854862) — генерация reusable checking-функций). AeroBIM оставляет LLM advisory-only: `summary.passed` пишет детерминированный контур (ADR-001). Гибрид для Самолёта/экспертизы: черновик замечания и IDS — да; выбор tool и generated checker на Shared-gate — нет, пока нет journal + hashed/`approval_ref` pack. Не говорить «мы лучше Iversen». Их F1 — не наша цифра. Они закрывают оцифровку нормы моделью; мы — кто имеет право сказать pass.
2. **Мандат уже есть — скоуп честно.** Сингапур: CORENET X обязателен с 01.10.2025 для новых проектов GFA ≥ 30 000 м²; **с 01.10.2026 — для новых GFA ≥ 5 000 м²**, ниже порога — добровольно ([URA/BCA circular 23.07.2026, dc26-08](https://www.ura.gov.sg/guidelines/circulars/dc26-08/)). Это **не** «все проекты». Питч Самолёту: прицеливаться в контур экспертизы, не в ручную замену эксперта.
3. **Геометрию не обещаем.** [Xiao et al., AuC 189](https://doi.org/10.1016/j.autcon.2026.107038) как раз закрывают geometry-intensive пожарные нормы графом. У нас это RT-003 `NOT_VERIFIED`. [Cheung et al., BRI](https://doi.org/10.1080/09613218.2026.2686293): ACC объясним, когда evidence и движок совпадают — это рамка нашего finding-контракта, не сертификат.

## 2. Мировые практики

| Модель | Прецедент (сверка 02.09.2026) | Урок для AeroBIM |
|---|---|---|
| Мандат регулятора | [CORENET X](https://info.corenet.gov.sg/overview/corenet-x-submission-portal/model-checker): IFC+SG Model Checker (schema → quality MVP → regulatory later, BCF). Мандат Gateway: ≥30 000 м² с 01.10.2025; **≥5 000 м² с 01.10.2026**; ниже 5 000 м² — добровольно ([URA dc26-08](https://www.ura.gov.sg/guidelines/circulars/dc26-08/)). Циркуляр также сообщает «более 140 проектов / около 300 фирм» — **их** KPI, не наш | Внедрение сверху. Не говорить «все проекты с октября 2026» |
| AI-движок как сервис | [FORNAX](https://lagosepppsfornax.eppps.com/) — коммерческое ответвление e-PlanCheck. Слоган «world's first AI plan checking» — **их** маркетинг | Путь «гос-движок → продукт» реален; не наш слоган |
| Реестр вместо бумаги | Эстония EHR / e-construction: процедуры и разрешения ведутся в [регистре](https://www.ttja.ee/ariklient/ehitised-ehitamine/ehitisregister-ehr); BIM-permit в развитии, не «уже вся страна» | Долгосрочно: проверка как запись, не файл-обмен. 10D-intake — предложение, не коннектор |
| Китайский масштаб | Госпрограммы цифрового РД-ревью и openBIM-checking (CBIMS / buildingSMART award 2023 — [Tsinghua](https://www.tsinghua.edu.cn/info/1180/107006.htm)). [Синьцзян 2026, 2D+3D онлайн](https://zjt.xinjiang.gov.cn/xjzjt/c113459/202604/94ce9ee035834329b612a759eada8b17.shtml). **«20 000+ моделей / 1000+ проектов» — UNVERIFIED** на эту дату (первичка не найдена) | Аналог обязательного РД-ревью. Не произносить 20k как факт |
| Solibri | CheckPoint cloud (Xinaps/Verifi3D) | Вертикали + cloud; открытый evidence-first слой — ниша, не «лучше Solibri» |

**Кейс-слайд Самолёту (говорить вслух):** «Мир уже мандатит машинную проверку: Сингапур — порог GFA и IFC-checker; Китай — гос-контур РД-ревью; Эстония — разрешение как запись реестра. Россия может войти в этот контур открытым слоем. Это не KPI пилота и не RT CLOSED.»

## 3. Пробелы / novelty-окна (переоценка)

| Окно | Статус 02.09.2026 | Что появилось |
|---|---|---|
| Вердикт-нейтральность как свойство кода | **OPEN** | Iversen, Fuchs, Perov, Wang, Madireddy ставят LLM *в* decision/generation path. Запрета LLM на вердикт в прочитанном нет |
| Fail-closed к дрейфу форматов движков | **OPEN** | Литература по-прежнему не обсуждает SKIPPED→ERROR при смене версии ifctester/ifcopenshell |
| Evidence-объект как контракт находки | **OPEN** | Cheung даёт *институциональную* рамку evidence–engine; машиночитаемого honesty-контракта находки (rule/GUID/expected/observed/claim-level) в работах нет |
| RU-контур (21.101, МОГЭ IDS, РД-ревью) | **OPEN** | Мировая литература не покрывает. Корпус партнёра в git по-прежнему отсутствует |

## 4. Промт литрадара

Текст промта живёт в [`../ai/ACADEMIC_LIT_RADAR.md`](../ai/ACADEMIC_LIT_RADAR.md). Этот файл — обзор, не операторский промт.

## 5. Статус команд (02.09.2026)

1. **матрица + позиционирование** — этот файл v1.1.4 + tracked extract; пять Crossref-строк 02.09.2026.
2. Related-work preprint — девять исходных позиций сверены; Springer ML переклассифицирован; Fuchs = EC3, не тезис; Ishigaki smoke EXECUTED.
3. Кейс-слайд — CORENET **исправлен** (не «все проекты»). CBIMS 20k — UNVERIFIED.
4. Вклад draft — без «первый в мире»; n≥30 по-прежнему впереди (`t_manual_s` лабораторного журнала пуст).
5. Фактчек ссылок 02.09.2026 — [`LINK_FACTCHECK_2026_09.md`](LINK_FACTCHECK_2026_09.md); снимок, не точность продукта.
6. AI-trace 02.09.2026 — промт вынесен в `docs/ai/` (вариант А).
7. E-process — CLI fixture-monitor, не job GitHub Actions; arXiv 2501.03982 в docstring модуля, не в `CITATION.bib`. Порог VLM — [`../evidence/VLM_CONFIDENCE_TUNING_PROTOCOL_2026_09.md`](../evidence/VLM_CONFIDENCE_TUNING_PROTOCOL_2026_09.md) (не interim 0.60).
