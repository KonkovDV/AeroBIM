# IFC worker durable-execution verification — 2026-09

PR #87 implements an explicitly **at-least-once** Redis reliable queue with atomic publish/repair, `BLMOVE RIGHT LEFT` reservation, retained payload until terminal ACK, CAS/lease fencing, bounded retries and dead-letter exhaustion. Async reports use the durable job id, allowing recovery to adopt a report committed before a job-state commit rather than publish a duplicate.

Production Redis uses AOF with `appendfsync always`. This is an explicit local-disk durability boundary, not high availability or consensus storage.

Local verification on the PR head before publication:

- Ruff check: passed
- Ruff format check: passed
- strict mypy: passed
- backend pytest: 3334 passed, 27 skipped, 176 subtests passed
- Markdown links: passed
- docs metadata integrity: passed

Primary research basis:

- ExoFlow, OSDI 2023: https://www.usenix.org/system/files/osdi23-zhuang.pdf
- Redis reliable lists / LMOVE: https://redis.io/docs/latest/commands/lmove/
- Redis XAUTOCLAIM: https://redis.io/docs/latest/commands/xautoclaim
- Redis persistence: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
- NIST SP 800-190: https://doi.org/10.6028/NIST.SP.800-190
- Anjali, Caraza-Harter & Swift, VEE 2020: https://doi.org/10.1145/3381052.3381315

Residual gates remain: Redis host/disk HA, fresh per-job kernel isolation for untrusted multi-tenant IFC, formal external-adapter effect idempotency, and a Streams migration before unreviewed horizontal worker scale-out.
