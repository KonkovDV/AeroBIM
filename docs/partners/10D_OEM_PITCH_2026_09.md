<!-- claims-lint: allow-file reason="Internal OEM-boundary draft; git does not send mail; not CDE-ready BCF; NO_GO" -->
---
title: "10D file-boundary draft (owner-only send)"
date: "2026-09-03"
last_updated: "2026-09-03"
status: draft
version: "0.2.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Internal draft for a file/API boundary conversation. Git does not send mail.
  Roles, not personal names. Not CDE-ready BCF. Not a signed OEM. Not hardware
  LLM deny. Not a count of 10D customers. Checkpoint NO_GO.
---

# Черновик границы с СОД партнёра (файловый обмен)

Отправляет **владелец**, если решит. Адресат — продуктовый контур СОД партнёра
(роль, не ФИО в git). П. 2.2.2 ответов 25.08: прямая интеграция на MVP
**не требуется**.

## Что можно сказать

1. AeroBIM не заменяет СОД и не заменяет слой проверки модели, который у
   партнёра уже куплен. Движок отвечает на вопрос «согласован ли *комплект*
   по содержанию»: выбранные факты между IFC, листом и запиской.
2. Контракт на MVP: approved-папка или выгрузка на входе; HTML / JSON /
   структурный BCF ZIP на выходе. Импорт BCF в СОД партнёра —
   **непроверено**; сначала спросить, ест ли их контур BCF 2.1/3.0, и если
   нет — какой формат принимать.
3. LLM/VLM не пишут `summary.passed` (ADR-001). Исходящие advisory-вызовы
   на профиле заказчика запрещены политикой профиля, не «аппаратно».
4. Нулевой вход: без CAPEX и без двустороннего sync в прод.

## Что нельзя сказать

- «бесшовная загрузка BCF в 10D»;
- «аппаратный запрет LLM»;
- число внешних контрактов СОД как наша метрика;
- ускорение эскроу / экономия процентов без базового замера;
- точность продукта и SLA комплекта.

Связанные: [`../quality/K4_COMMERCIAL_PATH_2026_08.md`](../quality/K4_COMMERCIAL_PATH_2026_08.md) ·
[`SAMOLET_QUESTIONS_GROUNDED_2026_09_03.md`](SAMOLET_QUESTIONS_GROUNDED_2026_09_03.md) G1.
