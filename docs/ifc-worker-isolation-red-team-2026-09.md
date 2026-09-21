# IFC worker isolation — Red Team triage (2026-09)

## Decision

Production HTTP is producer-only for `POST /v1/analyze/project-package/submit`.
It writes the job and JSON request to Redis; `aerobim.worker` is the only deployed
consumer and executor. FastAPI `BackgroundTasks` is not used. Synchronous package
analysis is disabled in production compose.

## Controls

- Durable Redis payload plus ready/processing lists; no Python pickle.
- `BLMOVE RIGHT LEFT` reservation, terminal ACK, lease heartbeat and fencing token.
- Async report identity is the durable job id; recovery adopts an already committed report after the report/job commit crash gap.
- Missing/corrupt payloads become observable failures and exhausted leases become `DEAD_LETTER`.
- On restart, stale RUNNING jobs are failed/requeued and the unacked payload is retried.
- Worker container: non-root image, read-only rootfs, tmpfs, all Linux capabilities
  dropped, `no-new-privileges`, PID limit, 2 CPU limit and 3 GiB memory limit.
- Worker joins only an `internal: true` control network. It can reach Redis but has no
  default/external network. Advisory LLM/VLM egress is explicitly denied.
- API and worker share only the report volume and read-only input samples.

## Failure taxonomy

| Event | Observable outcome |
|---|---|
| analysis exception | FAILED (or DEAD_LETTER after retry budget) |
| cancel before claim | CANCELLED; worker does not execute |
| cancel/lost lease after report creation | report discarded; no success commit |
| worker SIGKILL / container OOM | heartbeat expires; recovery marks FAILED and retries the retained payload |
| duplicate delivery | QUEUED→RUNNING CAS plus lease owner fences the second runner |
| Redis publish failure | HTTP 503 and job is marked failed, never silently left queued |

## Residual risk / non-claims

- Compose limits are a cgroup/container boundary, not a formally verified sandbox.
- OOM and forced SIGKILL are indistinguishable from inside the killed process. The job
  is therefore classified conservatively as lease-expired/worker-lost; the orchestrator
  remains the source of truth for the exact `OOMKilled` reason.
- The worker needs Redis control-plane networking, so literal `network_mode: none` is
  incompatible with this queue topology. The internal network denies external egress.
- Shared report-volume writes still require store-level idempotency/fencing. The runner
  discards a report when lease ownership is lost, but storage atomicity remains in scope
  for deployment qualification.
- Local/test mode retains an explicit test-only inline compatibility path. No non-test
  deployment may use it; non-test startup already requires Redis.
- This closes the in-API async executor gap only. It does not establish customer SLA,
  production readiness, a customer accuracy claim, CDE proof, or `customer_go=true`.

## SOTA rationale

The design applies standard reliable-queue semantics (durable payload, reservation,
acknowledgement, redelivery), at-least-once execution with idempotent/fenced commit,
lease heartbeats, fail-closed terminal states, and container least privilege. A stronger
next step is a per-job child sandbox (fresh cgroup/namespace/seccomp profile) so one
malformed IFC cannot retain allocator state in a long-lived worker.


## SOTA evidence and decision

The queue is explicitly **at-least-once**. End-to-end safety comes from idempotent effects and fencing, not a claim that a broker executes arbitrary external effects physically once.

- ExoFlow (OSDI '23) requires durable checkpoints or idempotent external outputs for exactly-once-consistent results: <https://www.usenix.org/system/files/osdi23-zhuang.pdf>.
- Redis reliable lists use atomic move plus ACK; `BLMOVE` replaces deprecated `BRPOPLPUSH`: <https://redis.io/docs/latest/commands/lmove/>.
- Redis Streams (`XACK`, PEL, `XAUTOCLAIM`) is the migration target before horizontal multi-worker scale: <https://redis.io/docs/latest/commands/xautoclaim>.
- Production uses AOF `appendfsync always`; this is a local durability boundary, not HA consensus: <https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/>.
- NIST SP 800-190 supports least privilege, read-only roots, bounded networking and workload separation: <https://doi.org/10.6028/NIST.SP.800-190>.
- VEE '20 describes the isolation/performance trade-off among containers, gVisor and Firecracker; untrusted multi-tenant IFC should ultimately move to a fresh per-job gVisor/Kata/Firecracker-style boundary: <https://doi.org/10.1145/3381052.3381315>.

Proven here: atomic publish/repair, atomic reservation, terminal ACK, poison-payload attribution, bounded retries/dead-letter, CAS lease fencing, and deterministic report identity across the report/job commit gap. Not proven: Redis host/disk HA, host-kernel escape resistance, formal linearizability of every external adapter, or fair unreviewed multi-worker scale-out.
