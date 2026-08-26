<!-- claims-lint: allow-file reason="Unsigned Samolet acceptance profile template; RT-002 OPEN; not customer approval" -->
---
title: "Samolet Acceptance Profile v0.1 — unsigned template"
date: "2026-08-15"
status: draft
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Template for customer signature. Empty owner/date/hash.
  Public MOEXP IDS are a reference layer, not this profile.
  Checkpoint NO_GO. Does not close RT-002.
---

# Samolet Acceptance Profile v0.1 (черновик на согласование)

**Статус:** unsigned. `profile_owner` = null. `approval_date` = null. `profile_hash` = null.  
**RT-002:** **OPEN**, пока нет подписи / письменного согласования Самолёта.  
Публичные IDS МОГЭ / АГР / СПб — reference layer, не этот профиль.

Просим согласовать **не платформу**, а минимальный профиль приёмки для одного пилотного сценария: IFC + PDF + ТЗ, один раздел, одна ревизия, фиксированный набор правил. Эксперт остаётся ответственным за итоговое решение.

| Поле | Черновик (не утверждено) |
|---|---|
| Область применения | Один завершённый раздел ПД/РД, одна ревизия, жилой/согласованный тип объекта |
| Разделы документации | ПД/РД по scope memo; не «все тома проекта» |
| Допустимые форматы | IFC (схема как в HEADER выгрузки авторинга заказчика), PDF/2D той же ревизии, ТЗ/EIR текстом или таблицей |
| Версии IFC | Как в файле заказчика; без алиаса IFC4↔IFC4X3 |
| Редакция IDS | Заказчика (`pack_hash`); МОГЭ IDS = reference only |
| Список норм | Только явно включённые edition/clause/jurisdiction |
| Severity policy | Critical / Warning / Info по правилам профиля, не по модели |
| Missing evidence | SKIPPED/NOT_VERIFIED не маскируется как PASS |
| DWG/DXF | Native DWG вне приёмки MVP; DXF sidecar ≠ DWG parser |
| MEP | Generic clash ≠ system-aware; `mep_system_clash=NOT_VERIFIED` без federated scope |
| Расчёты | Сверка величин; независимая корректность расчёта NOT_IMPLEMENTED |
| Исходы пакета | PASS / PASS_WITH_WARNINGS / REVIEW_REQUIRED / BLOCKED |
| Customer owner | *пусто — заполняет Самолёт* |
| Approval date | *пусто* |
| Hash profile | SHA-256 подписанного PDF/JSON после согласования |
| Подпись | *нет* |

**Definition of Done RT-002:** `customer_pack_hash != null` AND `profile_owner != null` AND `approval_date != null` AND scope memo signed AND norm edition/clause/jurisdiction complete. До этого product acceptance profile = BLOCKED.

Черновик профиля — этот файл. Подпись заказчика отсутствует.
