# Trusted commit-signing public keys

## Author keys (`*.asc` in this directory)

Count toward `signed_trusted` / ratio. Only these fingerprints are authorship.

| File | Short id | Role |
| --- | --- | --- |
| `B5690EEEBB952194.asc` | `B5690EEEBB952194` | Legacy author key |
| `24D8BC0C78AAABA6.asc` | `24D8BC0C78AAABA6` | Author key (`KonkovDV@users.noreply.github.com`) |

**Safe signing recipe (N-56):** sign with a key already listed here, **or** add the new `.asc` in the **same** commit that first uses it (that commit must still be signed by an *already* trusted author key — see N-59). A brand-new key alone yields local `G` and CI numerator **zero**; with `fail_on_unverifiable_signature` it is exit **2** (worse than unsigned).

## Platform keys (`platform/*.asc`)

Verify GitHub web-flow (and similar) merges so they are not `E`/`unverifiable`, but **do not** count toward the authorship ratio.

| File | Short id | Role |
| --- | --- | --- |
| `platform/4AEE18F83AFDEB23.asc` | `4AEE18F83AFDEB23` | GitHub web-flow commit signing — platform confirmation, not authorship |

After 2026-08-11 enforcement: prefer local merges signed by an author key, or accept web-merge as platform-verified without numerator credit.

## N-59 (active)

Changes under this tree may only land in a commit already signed by an author-trusted key. CI enforces this for commits after `n59_enforced_after` in `governance/commit_signing_policy.json` (filter-repo cliff: signatures cannot be recovered for rewritten history).
