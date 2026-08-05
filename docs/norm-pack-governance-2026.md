# Norm pack governance (2026)

## Rule lifecycle statuses

`draft` → `proposed` → `approved` → (`expired` | `superseded` | `not_applicable` | `requires_expert` | `blocked`)

LLM-generated text **cannot** auto-become `approved`.

## Required fields (engineering schema target)

`rule_id`, `source_document`, `edition`, `effective_from`/`to`, `official_url`, `clause`, `text`, `applicability`, `exceptions`, `mandatory`, `severity`, `execution`, `evidence_required`, `approval_ref`, `approved_by`, `approved_at`, `hash`.

## Current AeroBIM state (VERIFIED boundaries)

- RT-002 OPEN: customer-approved norm pack absent.
- Schema 2.0.0 + loader gates: `customer_approved` requires full approval object; deterministic rules need expert confirmation journal; `expert_required` is list-only.
- Engine can execute packs when provided; approval boundary enforced in code paths for proposed_by / profile.
- No claim of full СП/ГОСТ coverage.
- **P0 edition risk (2026-08-05):** **ГОСТ Р 21.101-2026** (приказ Росстандарта 12.02.2026 № 129-ст; в силу с 01.04.2026) заменяет **21.101-2020**. Docs/Exp B must not imply 2020 is current. Fixture packs currently lack explicit `21.101` rows — still flag any prose citations. See [`research/EXTERNAL_SOURCES_P1_P4_GOST_2026_08_05.md`](research/EXTERNAL_SOURCES_P1_P4_GOST_2026_08_05.md).
- ПП РФ № 87 (ред. 21.10.2025) / № 145 (правки 26.11.2025, эффекты 2026) — сверить при следующем norm-pack edit.

## RASE / IDS pipeline

Retrieval → extraction → normalization → interpretation → compilation → deterministic IDS → XSD/semantic validation → **human approval** → regression fixtures.

Stages after interpretation without approval = `proposed` only.
