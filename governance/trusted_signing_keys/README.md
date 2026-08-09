# Trusted commit-signing public keys (ASCII-armored)

Public material only. CI imports every `*.asc` here and marks them ultimately
trusted in an ephemeral runner keyring before `verify_commit_signatures.py`.

| File | Fingerprint (short) | Notes |
| --- | --- | --- |
| `B5690EEEBB952194.asc` | `B5690EEEBB952194` | Signs merge commits #12/#13/#14. Keyserver UID may read `GitHub <noreply@github.com>`; fingerprint must match `git log --show-signature`. |

Do not store private keys here.
