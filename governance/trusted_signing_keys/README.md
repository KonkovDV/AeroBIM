# Trusted commit-signing public keys

## Author keys (`*.asc` in this directory)

Count toward `signed_trusted` / ratio. Only these fingerprints are authorship.

| File | Short id | Role |
| --- | --- | --- |
| `B5690EEEBB952194.asc` | `B5690EEEBB952194` | Legacy author key (merges #12/#13/#14; secret on other machine) |
| `24D8BC0C78AAABA6.asc` | `24D8BC0C78AAABA6` | Author key on primary Windows workstation (`KonkovDV@users.noreply.github.com`) |

**Safe signing recipe (N-56):** sign with a key already listed here, **or** add the new `.asc` in the **same** commit that first uses it (that commit must still be signed by an *already* trusted author key — see N-59). A brand-new key alone yields local `G` and CI numerator **zero**; with `fail_on_unverifiable_signature` it is exit **2** (worse than unsigned).

### Operator: enable signing with the anchor key (do this locally)

Git config is not changed by automation by default. On the machine that pushes to `main` (this workstation uses `24D8BC0C78AAABA6`):

```
git config --local user.signingkey 24D8BC0C78AAABA6
git config --local commit.gpgsign true
git config --local gpg.program "C:/Program Files/Git/usr/bin/gpg.exe"
```

Upload **`24D8BC0C78AAABA6.asc`** to https://github.com/settings/keys (Title e.g. `AeroBIM workstation`). UID is already `KonkovDV@users.noreply.github.com` — that removes the `noreply@github.com` Unverified mismatch from the old `B5690` key. Keep `B5690` uploaded too if you still sign from the other machine.

**If GitHub shows the old key with `noreply@github.com` + Unverified:** that UID is not a
verifiable account email. Prefer the new workstation key above, or on the PC that holds the **B5690 secret** run `.\scripts\fix_b5690_github_uid.ps1`.

## Platform keys (`platform/*.asc`)

Verify GitHub web-flow (and similar) merges so they are not `E`/`unverifiable`, but **do not** count toward the authorship ratio.

| File | Short id | Role |
| --- | --- | --- |
| `platform/4AEE18F83AFDEB23.asc` | `4AEE18F83AFDEB23` | GitHub web-flow commit signing — platform confirmation, not authorship |

After 2026-08-11 enforcement: prefer local merges signed by an author key, or accept web-merge as platform-verified without numerator credit.

## N-59 (deferred)

Changes under this tree should only land in commits already signed by an author-trusted key. Tracked in `deferred_controls_registry.json` (`activates_on` after KT#2 freeze).
