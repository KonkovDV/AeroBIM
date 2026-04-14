# AeroBIM Wave 3 Async Project Package Jobs Design

## Goal

Add a minimal async execution surface for `analyze/project-package` so larger validations no longer require the caller to keep a single HTTP request open until report generation completes.

## Problem

`POST /v1/analyze/project-package` is currently synchronous.

That works for small inputs, but it does not scale to larger project packages where drawing analysis, optional clash detection, and report persistence may take noticeably longer than an interactive request budget.

## Decision

Introduce a same-process background job path for the existing use case instead of adding an external queue.

Chosen first slice:

- `POST /v1/analyze/project-package/submit`
- `GET /v1/analyze/project-package/jobs/{job_id}`

Chosen execution model:

- FastAPI `BackgroundTasks` for same-process deferred execution;
- singleton in-memory job store for runtime job status;
- existing `AnalyzeProjectPackageUseCase` remains the source of validation truth.

Official evidence checked:

- FastAPI `BackgroundTasks` docs confirm it is suitable for small same-process post-response work;
- FastAPI response docs confirm `202 Accepted` is the correct status for accepted async work.

## Contract Shape

Job status model fields:

- `job_id`
- `request_id`
- `status` = `queued | running | succeeded | failed`
- `created_at`
- `started_at`
- `completed_at`
- `report_id`
- `error_message`

Response helper fields added by the HTTP layer:

- `status_url`
- `report_url` when `report_id` exists

## Execution Flow

1. submit endpoint resolves and validates safe file paths from the request body;
2. submit use case creates a queued job record;
3. FastAPI schedules the runner with `BackgroundTasks`;
4. runner marks job `running`, executes the existing synchronous `AnalyzeProjectPackageUseCase`, then stores either `succeeded(report_id)` or `failed(error_message)`;
5. polling endpoint exposes the current job state.

## Persistence Strategy

This first slice keeps job state in memory only.

That is intentional:

- smallest sound implementation;
- zero new database or filesystem schema;
- suitable for the same-process operator workflow already used by the standalone stack.

Explicit limitation:

- jobs disappear on process restart.

## Layering

- domain: async job model + job store port;
- application: submit/status use cases + background runner service;
- infrastructure: in-memory job store adapter;
- presentation: submit/status endpoints only.

## Explicit Deferrals

- no multi-process queue;
- no retry orchestration;
- no persisted job history;
- no cancel endpoint;
- no frontend polling UI in this tranche.

## Verification Plan

- API tests for submit `202 Accepted`, status polling, success path, and failure path;
- changed-file diagnostics;
- targeted backend suite for job endpoints and existing sync report path;
- docs sync for Wave 3 execution status.