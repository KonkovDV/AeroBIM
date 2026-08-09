# Trusted commit-signing public keys

## Author keys (`*.asc` in this directory)

Count toward `signed_trusted` / ratio. Only these fingerprints are authorship.

| File | Short id | Role |
| --- | --- | --- |
| `B5690EEEBB952194.asc` | `B5690EEEBB952194` | Author / machine key for merges #12/#13/#14 |

**Safe signing recipe (N-56):** sign with a key already listed here, **or** add the new `.asc` in the **same** commit that first uses it (that commit must still be signed by an *already* trusted author key — see N-59). A brand-new key alone yields local `G` and CI numerator **zero**; with `fail_on_unverifiable_signature` it is exit **2** (worse than unsigned).

## Platform keys (`platform/*.asc`)

Verify GitHub web-flow (and similar) merges so they are not `E`/`unverifiable`, but **do not** count toward the authorship ratio.

| File | Short id | Role |
| --- | --- | --- |
| `platform/4AEE18F83AFDEB23.asc` | `4AEE18F83AFDEB23` | GitHub web-flow commit signing — platform confirmation, not authorship |

After 2026-08-11 enforcement: prefer local merges signed by an author key, or accept web-merge as platform-verified without numerator credit.

## N-59 (deferred)

Changes under this tree should only land in commits already signed by an author-trusted key. Tracked in `deferred_controls_registry.json` (`activates_on` after KT#2 freeze).
