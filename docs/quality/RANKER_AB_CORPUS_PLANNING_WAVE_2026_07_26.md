---
title: "Ranker A/B (paired nDCG) + adjudication corpus planning"
status: done
version: "1.0.0"
last_updated: "2026-07-26"
claim_boundary: "Fixture-вердикты ранкеров и размер корпуса разметки; никакого предсказания точности; RT-001 неизменен. Checkpoint остаётся NO_GO."
---

# Waves P & Q — Ranker A/B comparison + corpus planning (2026-07-26)

## External anchors (Jul 2026)

| Domain | Anchor |
|---|---|
| Paired eval design + power | **Miller 2024, arXiv 2411.00640 «Adding Error Bars to Evals»** (Anthropic) — pairing убирает общую сложность кейса из дисперсии; power-анализ как норма отчётности evals |
| Interval choice | **Brown, Cai & DasGupta 2001** (Statistical Science) — интервал **Wilson 1927** рекомендован против Wald/Clopper–Pearson практически при всех n, p |
| Exact test | Точный односторонний биномиальный тест (консервативный критический k), мощность из биномиального хвоста через `math.comb` — без нормальной аппроксимации |
| Discreteness | Chernick & Liu 2002 — пилообразность точной мощности по n; планировщик возвращает наименьший n и документирует это |
| Per-case metric | McSherry & Najork 2008 tie-aware nDCG (Wave N) как скаляр кластера |

## Wave P — A/B сравнение ранкер-профилей (закрывает долг Wave N)

Wave N отложила paired-сравнение «до появления второго ранкера» — но два
реальных профиля уже есть: `compute_issue_priority("default")` и
`("samolet")`. Теперь их можно сравнивать статистически честно.

- `eval_statistics`: `paired_scalar_permutation_test` (sign-flip на
  per-case скалярах; exact n≤12, add-one MC; two_sided/less/greater;
  finite-валидация — урок RT-B) и `paired_scalar_bootstrap_diff_ci`.
- `tools/compare_ranker_profiles.py`: два `ranking_quality_labels` над
  одним множеством кейсов/находок/грейдов (различия только в
  `priority_score`; расхождение грейдов = ошибка — защита от сравнения
  разных вселенных); per-case tie-aware nDCG@5/@10/full → paired
  permutation + bootstrap CI + Holm по семейству cutoffs; primary
  endpoint — `ndcg_full`; undefined-кейсы (IDCG=0) исключаются идентично
  с обеих сторон (грейды совпадают по построению — пары не рвутся).

## Wave Q — планировщик корпуса разметки («пороги не из воздуха»)

Checkpoint #2 требует пороги письменно; протокол Самолёта задаёт interim
TP/(TP+FP) ≥ 0.60, но **нигде не сказано, сколько размечать**. Теперь:

- `domain/study_design.py`: `wilson_interval`,
  `required_n_for_wilson_halfwidth`, `binomial_power_one_sided`
  (критический k: наименьший с P(K≥k|p₀)≤α; attained alpha репортится),
  `required_n_for_power`.
- `tools/plan_adjudication_corpus.py` — один вызов → артефакт
  `adjudication_corpus_plan`: power-дизайн + width-дизайн +
  пре-регистрированный decision preview (какие наблюдённые счётчики
  докажут порог по нижней границе Wilson).

**Числа для пилотных дефолтов** (p₀=0.60, ожидание 0.75, α=0.05, power=0.8):

| Дизайн | n | Примечание |
|---|---|---|
| Exact binomial power | **62** | критерий: ≥44 подтверждённых из 62; мощность 0.812; attained α ≤ 0.05 |
| Wilson half-width ≤ 0.08 | **111** | доминирует |
| **Рекомендация** | **111** | при 83/111 (0.75) нижняя граница Wilson ≈ 0.66 > 0.60 — порог доказан |

## Tests (18, ручные эталоны)

Scalar permutation перечислен вручную (n=2: p=2/4; less: 1/4); Wilson
классика 5/10 → (0.2366, 0.7634) с точным центром 0.5; биномиальный хвост
n=20, p₀=0.5 просуммирован вручную (21700/2²⁰ → k*=15), мощность при
p=0.8 ≈ 0.804 (табличное значение); smallest-n семантика проверена
(n−1 не добирает мощность); A/B: flat-vs-perfect → exact p=2/1024,
идентичные профили → p=1; tamper грейда → ошибка.

## Explicitly NOT claimed

- Планировщик не предсказывает точность — только размер усилия разметки.
- Sample-size для κ/α (Donner–Eliasziw и родственные) не реализован:
  требует модели маргинальных распределений разметчиков — отдельное
  решение, не «формула на сдачу».
- Betting e-process (долг Wave O) не закрыт этой волной — остаётся
  задокументированным трейд-оффом.

## Gate evidence (2026-07-26 local)

`ruff format/check` PASS · `mypy src` 202 files PASS · `pytest tests -q`
**1087 passed, 7 skipped**.
