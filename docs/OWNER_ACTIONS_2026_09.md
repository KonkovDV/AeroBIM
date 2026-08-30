<!-- claims-lint: allow-file reason="Owner actions git cannot close; not claimed done; NO_GO" -->
---
title: "Owner actions — what git does not close (September 2026)"
date: "2026-08-30"
last_updated: "2026-08-30"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Checklist of owner acts. Rows are not marked done. Git does not send mail,
  fill i.moscow names, or verify Fund PDFs. Checkpoint NO_GO.
---

# Действия владельца (git не закрывает)

Ни одна строка не утверждает, что действие уже сделано. Признак выполнения
ставит капитан вне git.

| ID | Действие | Критерий | Срок | Признак выполнения |
|---|---|---|---|---|
| OA-1 | Письмо партнёру: обложка протокола 0,60 «готово подписать» | К3, Б1, Б2 | до окна КТ#3 (03–21.09) | Есть исходящее письмо; `partner_kpis_agreed_in_writing` станет True **только** после подписи партнёра, не после отправки |
| OA-2 | ФИО и два класса компетенций в заявке i.moscow | К1 | до защиты по отбору/финалу | Ячейки «кто» в форме заполнены капитаном; шаблон git остаётся без ФИО |
| OA-3 | Сверить PDF приказа и Положения с [`ORDER_WEIGHTS_VERIFICATION_2026_09.md`](quality/ORDER_WEIGHTS_VERIFICATION_2026_09.md) | attributed → verified веса | до речи, где называем веса как факт приказа | Колонка «В PDF» заполнена; статус строк не UNVERIFIED |
| OA-4 | Вопрос организаторам по п. 6.3 и Приложению 3 Положения | Б5; система B | до соглашения о призе | Письмо с нейтральной формулировкой; LICENSE не меняем |
| OA-5 | Привлечь двух независимых разметчиков (~100 находок) | Б2 полка; RT-001 протокол | до любого publishable precision | Два человека названы **в заявке / письме**, не выдуманы в git; κ ещё не цифра продукта |
| OA-6 | Подтвердить venue Perov «From Regulations to IDS»: ICDMW DOI vs *Buildings* 15 art. 2927 | К2 научная база | до защиты, если цитируем | Одна каноническая ссылка или явная пометка «две публикации» |

Обложка письма: [`partners/PARTNER_PROTOCOL_SIGNREADY_COVER_2026_08.md`](partners/PARTNER_PROTOCOL_SIGNREADY_COVER_2026_08.md).
Шаблон К1: [`partners/K1_ROLE_MATRIX_TEMPLATE_2026_08.md`](partners/K1_ROLE_MATRIX_TEMPLATE_2026_08.md).
ADR развилки прав: [`architecture/ADR-004-prize-ip-mit-fork-2026.md`](architecture/ADR-004-prize-ip-mit-fork-2026.md).
План разметки: [`evidence/DEFECT_INJECTION_RECALL_PLAN_2026_09.md`](evidence/DEFECT_INJECTION_RECALL_PLAN_2026_09.md).

`predicted_aerobim_total() is None`. Checkpoint **NO_GO**.
