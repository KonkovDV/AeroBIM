# IFC worker durable-execution verification — 2026-09

PR #87 implements an explicitly **at-least-once** Redis reliable queue with atomic publish/repair, `BLMOVE RIGHT LEFT` reservation, retained payload until terminal ACK, CAS/lease fencing, bounded retries and dead-letter exhaustion. Async reports use the durable job id, allowing recovery to adopt a report committed before a job-state commit rather than publish a duplicate.

The tested implementation was integrated onto current `main` at commit `75bee57b332f4f5afad4b5113cf2f08887629b45`, preserving the later jury README corrections. Integration workflow run `35692360870` completed successfully and removed its temporary bootstrap workflow from the final tree.

Production Redis uses AOF with `appendfsync always`. This is an explicit local-disk durability boundary, not high availability or consensus storage.

Verification:

- Ruff check: passed
- Ruff format check: passed
- strict mypy: passed
- backend pytest: passed (`3330 passed`, `29 skipped`, `176 subtests passed` on the integrated current-main tree)
- production Compose configuration: parsed successfully on GitHub Actions
- malformed/non-object reserved payload regression cases: passed
- Markdown links: passed
- docs metadata integrity: passed
- CI-generated runtime baseline adopted from run `35658840115`

Primary research basis:

- ExoFlow, OSDI 2023: https://www.usenix.org/system/files/osdi23-zhuang.pdf
- Redis reliable lists / LMOVE: https://redis.io/docs/latest/commands/lmove/
- Redis XAUTOCLAIM: https://redis.io/docs/latest/commands/xautoclaim
- Redis persistence: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
- NIST SP 800-190: https://doi.org/10.6028/NIST.SP.800-190
- Anjali, Caraza-Harter & Swift, VEE 2020: https://doi.org/10.1145/3381052.3381315

Residual gates remain: Redis host/disk HA, fresh per-job kernel isolation for untrusted multi-tenant IFC, formal external-adapter effect idempotency, and a Streams migration before unreviewed horizontal worker scale-out.
