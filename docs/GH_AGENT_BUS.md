# Шина работы через GitHub

Несколько сессий могут брать задачи из одного репозитория. Очередь — issue.
Код меняется только pull request. Статус задачи — один JSON-комментарий.
Второй канал статуса не заводить: ни Discussions, ни Wiki, ни доска как
единственный источник.

Протокол `aerobim.agent_bus.v1`. Проверка формы комментария, треда и прогона:

```text
python -m aerobim.tools.agent_bus check-comment comment.md
gh issue view N --json comments > comments.json
python -m aerobim.tools.agent_bus check-thread N comments.json
gh api repos/KonkovDV/AeroBIM/actions/runs/ID --jq "{status,conclusion}" > run.json
gh api repos/KonkovDV/AeroBIM/actions/runs/ID/jobs > jobs.json
python -m aerobim.tools.agent_bus check-run run.json jobs.json
```

## Четыре слоя

1. `main` хранит код и границы продукта.
2. Issue хранит очередь: claim, heartbeat, blocked, handoff, steal, done.
3. Pull request — единственное изменение кода.
4. Checks решают, можно ли вливать. Красный PR не вливать.

Облачная сессия не видит локальные комплекты заказчика. Таких файлов в git нет.

## Вход

```text
git fetch origin && git checkout main && git pull --ff-only
gh issue list --search "label:agent-bus is:open -label:claimed" --limit 20
gh issue view N --json title,labels,parent,subIssues,blockedBy,blocking,comments
```

Сначала этот файл, затем [границу заявления](pilot-claim-boundary-2026.md) и тело issue.
Работу не начинать, пока claim не записан и комментарии не перечитаны.

Свежесть кода:

```text
git rev-parse HEAD
```

Если `base_sha` в claim не совпадает с `origin/main`, claim устарел.

## Комментарий

Один комментарий — один объект. Операции: `claim`, `heartbeat`, `blocked`,
`handoff`, `steal`, `done`.

````markdown
### AGENT_BUS aerobim.agent_bus.v1
```json
{
  "schema": "aerobim.agent_bus.v1",
  "op": "claim",
  "issue": 12,
  "agent": "local-session",
  "host": "local",
  "base_sha": "REPLACE_WITH_origin_main_sha",
  "branch": "feat/12-short-name",
  "until": "2026-09-24T14:00:00+03:00"
}
```
````

`host` — `local` или `cloud`. Ветка не `main`. `until` с часовым поясом.

````markdown
### AGENT_BUS aerobim.agent_bus.v1
```json
{
  "schema": "aerobim.agent_bus.v1",
  "op": "done",
  "issue": 12,
  "agent": "local-session",
  "pr_url": "https://github.com/KonkovDV/AeroBIM/pull/12",
  "ci_run_id": "https://github.com/KonkovDV/AeroBIM/actions/runs/1",
  "sha": "MERGE_SHA",
  "test_quality_gate": [
    "тест вызывает функцию продукта",
    "pytest.skip не считается покрытием",
    "нет assert True"
  ]
}
```
````

## Правила

- **claim.** Первый валидный JSON на открытом issue без метки `claimed`
  побеждает. Сразу `gh issue edit N --add-label claimed`, затем ещё раз
  прочитать комментарии. Если более ранний claim другого `agent`, остановиться
  и не пушить. Повторное чтение не делает запись атомарной. Ветка
  `feat/<issue>-<slug>` от `origin/main`. Draft PR — после первого push.
- **heartbeat.** Не реже раза в 6 часов, пока нет зелёного PR.
- **steal.** Только если между последним сигналом держателя и этим
  комментарием прошло не меньше 6 часов, и в ветке нет коммитов после claim.
  Часы считает `createdAt` комментария. Поле `stale_heartbeat_hours` само по
  себе steal не выдаёт. Чужую ветку не переписывать.
- **blocked.** `reason` и номера issue. Связь:
  `gh issue edit N --add-blocked-by M`.
- **handoff.** SHA, URL PR, что сделано, что осталось. Снять `claimed`.
  После handoff issue снова без держателя.
- **done.** После merge в `main`. `ci_run_id` обязателен. Done снимает
  держателя. Issue закрывать
  строкой `Closes #N` только когда критерии выхода выполнены. Иначе
  `Relates to #N`.

Комментарий не содержит `summary_passed` и не ставит `customer_go`.

## Зелёный CI

Номер run сам по себе не прогон. Бывает `conclusion=success` при
`runner_id=0`, пустом `runner_name` и `steps=[]`. Такой run не зелёный.
`gh run view --json jobs` на hosted runner оставляет `runnerId` пустым даже
у живого прогона. Это не доказательство runner. Берутся `status` и
`conclusion` прогона и jobs API (`runner_id`, `runner_name`, `steps`).

Run зелёный, только если:

1. `status=completed` и `conclusion=success`.
2. У jobs `lint`, `typecheck`, `test`, `pytest-readme-extras`, `frontend`,
   `baseline-integrity`: `conclusion=success`, `runner_id` не 0,
   `runner_name` не пустой, и хотя бы один step с `conclusion=success`.

Draft снимать после этого. Локальный pytest не заменяет `ci_run_id`.
Pin baseline пишет job `baseline-integrity`, не локальная сессия.

## Качество теста

| Проверка | Годится | Не годится |
|---|---|---|
| Вызов | функция продукта на фикстуре | mock на пути вердикта |
| Пропуск | причина до assert, если API нет | `pytest.skip` вместо результата |
| Утверждение | конкретное поле | `assert True` |
| Прогон | URL run с живым runner | номер run без steps |

## Границы продукта

- Модель не пишет `summary.passed`. Вердикт собирает EvidenceAssembler.
- `customer_go` остаётся false. Шина это не переключает.
- Локальный прогон не становится pin. В pin попадает артефакт CI.
- Импорт BCF в СОД в коде `NOT_VERIFIED`.
- Точность продукта, срок заказчика и поставленный MEP в комментарии не заявлять.

## Чего здесь нет

Конкурсная матрица, PDF комплекта и отдельный брокер сообщений к этой шине
не относятся. Очередь анализа IFC в продукте — worker и Redis. Это другой
контур: он исполняет задачу анализа, а не делит работу между сессиями.
