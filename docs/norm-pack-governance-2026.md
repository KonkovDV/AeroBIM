# Norm pack governance (2026)

## Rule lifecycle statuses

`draft` → `proposed` → `approved` → (`expired` | `superseded` | `not_applicable` | `requires_expert` | `blocked`)

LLM-generated text **cannot** auto-become `approved`.

## Required fields (engineering schema target)

`rule_id`, `source_document`, `edition`, `effective_from`/`to`, `official_url`, `clause`, `text`, `applicability`, `exceptions`, `mandatory`, `severity`, `execution`, `evidence_required`, `approval_ref`, `approved_by`, `approved_at`, `hash`.

## Current AeroBIM state (VERIFIED boundaries)

- RT-002 OPEN: customer-approved norm pack absent.
- Engine can execute packs when provided; approval boundary enforced in code paths for proposed_by / profile.
- No claim of full СП/ГОСТ coverage.

## RASE / IDS pipeline

Retrieval → extraction → normalization → interpretation → compilation → deterministic IDS → XSD/semantic validation → **human approval** → regression fixtures.

Stages after interpretation without approval = `proposed` only.
