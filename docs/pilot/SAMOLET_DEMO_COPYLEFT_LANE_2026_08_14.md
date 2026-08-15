<!-- claims-lint: allow-file reason="Samolet-local copyleft lane; forbidden phrases as non-claims; NO_GO" -->
---
title: "Полоса copyleft только для показа Самолёту"
date: "2026-08-14"
claim_boundary: >
  Local demo lane. GPLv3 IFC may be read from gitignored .local/.
  Not vendored. Not Docker. Not other customers. Not native DWG.
  Not product accuracy. Checkpoint NO_GO.
closes_rt001: false
closes_rt002: false
closes_rt003: false
---

# Copyleft только для показа Самолёту

Публичный репозиторий и поставка **остальным** остаются без токсичных лицензий (GPL-3 LibreDWG, GPLv3 IFC в git, AGPL в Docker).

Для **локального показа Самолёту** лицензия больше не повод выкидывать GPLv3-модели IFC-Bench с диска. Файлы живут в gitignored `.local/`. CI флаг отключает.

## Как включить (эта машина, не CI)

```bash
cd backend
python -m aerobim.tools.fetch_ifc_bench_v2 --include-gplv3 --samolet-demo-copyleft
python -m aerobim.tools.run_federated_mep_inventory --samolet-demo-copyleft
```

Вторая команда пишет только в `artifacts/` — не в `docs/evidence/`.

## Что это не снимает

| Тема | Статус |
|---|---|
| RT-001 / RT-002 / RT-003 | OPEN |
| Native DWG / LibreDWG | Не линкуем. Показ: IFC + PDF/A (или DXF от заказчика) |
| PyMuPDF AGPL | Optional extra `pdf-agpl` for legacy tools; KT#2 overlay uses **pypdfium2**. **Нет** в runtime lock / Docker |
| Checkpoint | **NO_GO** |

Политика: [`../license-policy-2026.md`](../license-policy-2026.md) § «Две полосы».
