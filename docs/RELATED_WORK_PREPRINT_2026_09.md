<!-- claims-lint: allow-file reason="Preprint related-work and third-party world-precedent citations; not AeroBIM volume or product accuracy; NO_GO" -->
---
title: "Related work for preprint — September 2026"
date: "2026-09-02"
last_updated: "2026-09-02"
status: active
version: "1.1.3"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Bibliography and third-party public programs. Not AeroBIM measured volume.
  Not partner hours. Not product accuracy. LLM remains advisory-only (ADR-001).
  Checkpoint NO_GO. Working radar with verification log:
  docs/quality/ACADEMIC_LIT_REVIEW_2026_09.md.
---

# Related-work (preprint) — сентябрь 2026

Цитаты для обзора. Не закрывают RT-001/002/003. Чужие объёмы и F1 не переносить.
Полный журнал сверки 02.09.2026: [`quality/ACADEMIC_LIT_REVIEW_2026_09.md`](quality/ACADEMIC_LIT_REVIEW_2026_09.md). Снимок ссылок: [`quality/LINK_FACTCHECK_2026_09.md`](quality/LINK_FACTCHECK_2026_09.md).

## Ближайший prior art (контраст вердикта)

| Работа | Где | Отношение к AeroBIM |
|---|---|---|
| [Iversen & Huang](https://www.sciencedirect.com/science/article/pii/S0926580525007472) | AuC 182 (2026) 106707; DOI `10.1016/j.autcon.2025.106707` | LLM на маршруте проверки (интерпретация → tool → отчёт). **Контр-позиция:** детерминированный `summary.passed`, LLM/VLM advisory (ADR-001). Их F1 — не наша цифра. |
| [Fuchs, Hellin, Borrmann](https://mediatum.ub.tum.de/doc/1854862) | EC3 Jul 2026 (не тезис) | Агенты **генерируют** checking-функции по IDS-validated требованиям. У AeroBIM hashed/`approval_ref` pack. |
| [Xiao et al.](https://doi.org/10.1016/j.autcon.2026.107038) | AuC 189 (2026) 107038 | Geometry-intensive CC (SGR-BIM, пожарные нормы). Дорожная карта RT-003 `NOT_VERIFIED`, не поставка. |
| [Zentgraf et al.](https://doi.org/10.1016/j.aei.2026.104735) | AEI 74C 104735 (май 2026) | STS/ISOProps → SHACL. DOI в [`docs.md`](docs.md) подтверждён. |
| [Madireddy et al.](https://doi.org/10.3390/electronics14112146) | Electronics 14(11) 2146 | LLM пишет Python под Revit. Native CAD; у нас IFC-first. |
| [Ishigaki-IDS-Bench](https://arxiv.org/abs/2605.22079) | arXiv:2605.22079 | Генерация IDS. Smoke AeroBIM = processability **gold** IDS 166/166, `open_bench_only`, не generation F1. |
| [BIM-Edit](https://arxiv.org/abs/2606.20146) | arXiv:2606.20146 | NL-edit IFC. Смежный бенч, не проверка комплекта. |
| [Simbola et al.](https://doi.org/10.1007/s10994-026-07038-6) | Mach Learn 115:116 (2026) | LLM-CC над **data-product** YAML, не строительные нормы. |
| [Cheung et al.](https://doi.org/10.1080/09613218.2026.2686293) | BRI, e-pub Jun 2026 | Институционализация ACC; evidence–engine alignment. Рамка discussion, не закрытие finding-контракта. |

## Смежный prior art (Crossref 02.09.2026; уже цитировались в репо)

Не закрывают ADR-001. Чужие метрики не переносить.

| Работа | Где | Отношение к AeroBIM |
|---|---|---|
| [Perov et al.](https://doi.org/10.1109/icdmw69685.2025.00203) | ICDMW 2025, 1696–1702 | Регламент → IDS (tool-augmented LLM). Рядом с Fuchs. Не склеивать с *Buildings* 15 art. 2927. |
| [Dias, Miceli Junior, Pellanda](https://doi.org/10.1016/j.autcon.2026.107043) | AuC 189 (2026) 107043 | IDS как information requirements для **сметы/QTO**. Analog, не IDScribe и не наш sell-path. |
| [Wang, Hwang, Han, Gupta](https://doi.org/10.1061/jcemd4.coeng-18122) | JCEM 152(8) 2026 | Generative AI-assisted compliance. LLM на маршруте требований; у нас advisory-only. |
| [Zhang et al.](https://doi.org/10.3390/buildings16040719) | Buildings 16(4) 719 | HITL semantic rule base. Близко к HITL-контуру; их eval не наш. |
| [SNOWTEC](https://doi.org/10.1016/j.mlwa.2026.100911) | MLWA 24 (2026) 100911 | IE норм → KG. Смежный extraction, не вердикт. |

## Eval-stats в репо (не ACC prior art)

CLI `python -m aerobim.tools.sequential_regression_monitor` — e-process по
сравнениям `extraction_quality_report` (калибраторы Vovk & Wang 2021; latch
по Ville; отказ необратим). **Не** подключён в `.github/workflows`. Только
история регрессий на **fixture**, не точность заказчика (RT-001). Фон:
[arXiv 2501.03982](https://arxiv.org/abs/2501.03982) / JRSS-B `qkag050`
(anytime validity). Это не опубликованная статья AeroBIM и не «мы лучше Iversen».

## Вклад (draft) и три тезиса жюри

**Draft (не «первый в мире», не метрика партнёра):** open-source IFC-pack acceptance gate, где (а) нейтральность вердикта к LLM доказуема кодом, (б) замечание — evidence-объект, (в) дрейф форматов движков fail-closes, (г) advisory под reproducibility-hash. После adjudication n≥30 добавить «и измерено на названном корпусе». Partner n = 0.

1. Поле ставит LLM на маршрут (Iversen — выбрать tool; Fuchs — сгенерировать функцию). Мы оставляем LLM вне `summary.passed`. Для Самолёта/экспертизы это не «мы лучше Iversen»: черновик замечания и IDS — да; выбор проверки и generated checker на Shared-gate — нет, пока pack не hashed/`approval_ref`. Они закрывают оцифровку нормы моделью; мы — кто имеет право сказать pass.
2. Мандат проверки уже существует: Сингапур CORENET X — с 01.10.2026 **новые проекты GFA ≥ 5 000 м²**, не все проекты ([URA dc26-08](https://www.ura.gov.sg/guidelines/circulars/dc26-08/)). Китай — гос-контур РД-ревью (объём «20k моделей» на 02.09.2026 **UNVERIFIED**). Эстония — разрешение как запись EHR.
3. Геометрию не обещаем (Xiao = карта RT-003). Cheung: ACC объясним, когда evidence и движок совпадают.

**EN skeleton:** We describe an open-source IFC-pack acceptance gate in which LLM/VLM outputs are excluded from `summary.passed` by construction, each finding is an evidence object, external engine format drift fail-closes, and advisory traces are origin-filtered under a reproducibility hash. Partner-pack accuracy remains unmeasured.

## Мировой прецедент (не наш объём)

- [CORENET X Model Checker](https://info.corenet.gov.sg/overview/corenet-x-submission-portal/model-checker) — IFC+SG; schema / quality MVP / regulatory later. Мандат Gateway: ≥30 000 м² с 01.10.2025; ≥5 000 м² с 01.10.2026; ниже — добровольно.
- Китай: программы цифрового РД-ревью; [Синьцзян 2026 2D+3D](https://zjt.xinjiang.gov.cn/xjzjt/c113459/202604/94ce9ee035834329b612a759eada8b17.shtml). «20 000+ / 1000+» не произносить, пока нет первички.
- Эстония: [EHR](https://www.ttja.ee/ariklient/ehitised-ehitamine/ehitisregister-ehr) — процедуры в регистре; BIM-permit в развитии.
- Solibri CheckPoint — вертикали + cloud; не «лучше Solibri глобально».

Рыночные CAGR **не** SAM (`tam_horizon_is_our_revenue() == False`).

## Что не цитировать как наше

- n измеренных партнёрских точек = 0.
- Лабораторный журнал — только `t_tool_ms`; `t_manual_s` пуст.
- RT-003: геометрия `NOT_VERIFIED`.
- Их F1 / «два месяца экономии» CORENET — чужие claims.
