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

CI must pass those secrets through **step `env:`**, not composite `with:`
inputs. GitHub truncates multiline action inputs at the first newline.
The list arrives only as secret `AEROBIM_KITCHEN_DENYLIST_B64` (base64 of the
LF-normalized list). A plaintext multiline secret is not accepted: that path
already dropped tokens against the pin.

Fail-closed: if the list or key is missing, or the digest does not match the pin,
`scripts/lint_claims.py` and the hygiene tests fail. The scan walks **tracked**
files (`git ls-files`) — the published tree. A hand list of content directories
is a class defect: the next guard in a new folder would be invisible. Service
dirs and quarantine prefixes are skipped. Hits report **paths only**.

The token scan reads overlapping byte windows (2 MiB) so a file between the
window size and the 50 MiB quarantine cap is still checked. Files that are not
UTF-8 are scanned as bytes. PDF and Office/ZIP members are also opened for a
text layer so a compressed locator is not a silent skip.

Invariant: guard modules are the denylist module plus every tracked `.py` file
that imports it. A hand list of guard paths is the same class defect as a hand
list of content roots. Markdown pointers stay covered by the full-tree scan.

Pack quarantine: tracked native authoring/solver/coordinator suffixes and
quarantine prefixes (`files/`, `.local/pack/`) plus a 50 MiB size cap. The
documented fake-byte DWG fixture under `samples/cad/` is the only suffix
allowance. Document formats (PDF/Office/ZIP) are extracted during the token
scan rather than blanket-quarantined, because the public tree already holds
documented fixtures in those formats.
