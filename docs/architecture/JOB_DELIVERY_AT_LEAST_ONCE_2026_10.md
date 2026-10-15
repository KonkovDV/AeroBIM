<!-- claims-lint: allow-file reason="Job delivery honesty; at-least-once; Checkpoint GO; customer_go false" -->
---
title: "Analyze job delivery — at-least-once"
status: active
version: "1.0.0"
last_updated: "2026-10-15"
---

# Analyze jobs: at-least-once, not exactly-once

Redis Streams / in-memory job stores move poison workers to `JobStatus.DEAD_LETTER`
after retries (lease exhausted or retries>3). The job record is **retained** and
visible via API polling / UI (`dead_letter` terminal status).

- Delivery: **at-least-once**. Do not claim exactly-once or «доставлено в СОД».
- `DEAD_LETTER` ≠ silent drop; operators must inspect and requeue/cancel explicitly.
- No second broker (RabbitMQ/outbox) is required for this honesty surface.

Checkpoint `GO`; `customer_go` false.
