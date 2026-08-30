<!-- claims-lint: allow-file reason="ADR-004: MIT vs prize exclusive-rights fork; LICENSE unchanged; NO_GO" -->
---
title: "ADR-004 — Prize exclusive rights vs MIT (no LICENSE change)"
date: "2026-08-30"
last_updated: "2026-08-30"
status: proposed
version: "0.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Records the IP fork in Regulation 6.3 vs LICENSE MIT. Does not change
  LICENSE. Does not promise a patent fence or a transfer of exclusive rights.
  Checkpoint NO_GO.
---

# ADR-004: исключительные права приза vs MIT

## Status

**Proposed.** LICENSE в репозитории остаётся **MIT**. Этот ADR ничего не
обещает партнёру и не правит `LICENSE`.

## Context

Атрибутированный п. 6.3 Положения: соглашение о призе **может** передать
исключительные права без доплаты к призу. PDF Положения в git нет; формулировка — owner briefing, статус сверки
UNVERIFIED, пока колонка PDF в
[`ORDER_WEIGHTS_VERIFICATION_2026_09.md`](../quality/ORDER_WEIGHTS_VERIFICATION_2026_09.md)
не заполнена.

ADR-002 фиксирует open-core границу и явно откладывает смену лицензии.
Б5 просит «полноту передачи результата». Обещать «права не уйдут» или
«патентный забор» git не имеет права.

## Decision (пока развилка, не выбор)

Ничего не менять в `LICENSE` до ответа организаторов и отдельного ADR
принятия. В речи: «ядро сейчас MIT; условия приза читаем в соглашении, когда
его дадут; исключительные права не обещаем и не отрицаем заранее».

## Options considered

| Вариант | Суть | Последствия |
|---|---|---|
| A. Молчать | Не поднимать 6.3 | Риск сюрприза на соглашении; Б5 выглядит неготовым |
| B. Зафиксировать развилку (этот ADR) | Вопрос организаторам; LICENSE без изменений | Честность Б5; нет юридического обещания |
| C. Сменить LICENSE сейчас | Dual / proprietary | Ломает вклад MIT; нет текста соглашения |
| D. Обещать, что права не передадим | Конфликт с возможным 6.3 | Ложь, если Положение подтвердится |

**Сейчас:** B. Выбор A/C/D — владелец после PDF и письма Фонда.

## Consequences

- BOM и ticksheet Б5 ссылаются сюда, не на «IP закрыт».
- Вопрос организаторам — строка OWNER_ACTIONS, не коммит.
- `exclusive_rights_may_transfer_under_6_3` в SSOT остаётся **True** как
  риск программы, не как свершившийся факт.

Связанные: [`ADR-002-open-core-commercial-boundary-2026.md`](ADR-002-open-core-commercial-boundary-2026.md) ·
[`KT3_DELIVERY_BOM_2026_08.md`](../quality/KT3_DELIVERY_BOM_2026_08.md).
