<!-- claims-lint: allow-file reason="Kitchen denylist pin contract; no protected literals; NO_GO" -->
---
title: "Kitchen denylist pin (publication gate)"
date: "2026-08-28"
last_updated: "2026-08-28"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Describes the out-of-git denylist gate. Does not list protected tokens.
  Checkpoint NO_GO.
---

# Kitchen denylist pin

Protected literals (pack-share host locator and related kitchen strings) are **not**
in git. The committed pin is `audit/evidence/kitchen-denylist.pin.json`: token
**count** plus HMAC-SHA256 of the sorted list. The HMAC key and the list itself
live in `.local/` (local) or GitHub Actions secrets (CI).

Fail-closed: if the list or key is missing, or the digest does not match the pin,
`scripts/lint_claims.py` and the hygiene tests fail. The scan walks **tracked**
files (`git ls-files`) — the published tree — with no manual content-root list.
Service dirs and quarantine prefixes are skipped. Hits report **paths only**.

Invariant: guard modules listed in `scripts/kitchen_denylist.py` (`GUARD_RELATIVE`)
must not embed denylist literals.

Pack quarantine: tracked native authoring/solver/coordinator suffixes and
quarantine prefixes (`files/`, `.local/pack/`) plus a 50 MiB size cap. The
documented fake-byte DWG fixture under `samples/cad/` is the only suffix
allowance.
