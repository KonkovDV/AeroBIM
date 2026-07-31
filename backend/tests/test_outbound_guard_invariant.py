"""P-017 outbound guard invariant: every network call outside tools/ must go
through the SSRF-guarded ``safe_urlopen`` seam.

VERIFIED baseline 2026-07-31: bsi_validation_service, http_bcf_api_client,
kimi_k3_advisory_client, and oidc_token_validator all call
``core.security.outbound_url.safe_urlopen`` (host check + DNS pin + no
redirects). The only raw ``urlopen`` lives in ``tools/run_live_review_smoke.py``
(local smoke against the developer's own server). This guard keeps raw outbound
primitives from creeping back into shipped layers.
"""

from __future__ import annotations

import re
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src" / "aerobim"
# Raw outbound primitives that bypass the SSRF guard.
_RAW = re.compile(
    r"(?<!safe_)urlopen\(|requests\.(?:get|post|put|delete|request)\(|httpx\.(?:get|post|Client|AsyncClient)\("
)
_ALLOWED = (
    "core/security/outbound_url.py",  # the guard implementation itself
    "tools/",  # developer tools may hit their own local server
)


def _violations() -> list[str]:
    found: list[str] = []
    for path in sorted(_SRC.rglob("*.py")):
        rel = path.relative_to(_SRC).as_posix()
        if rel.startswith(_ALLOWED) or rel in _ALLOWED:
            continue
        text = path.read_text(encoding="utf-8")
        for match in _RAW.finditer(text):
            found.append(f"{rel}: raw outbound call {match.group(0)!r}")
    return found


def test_shipped_layers_never_bypass_ssrf_guard() -> None:
    violations = _violations()
    assert not violations, (
        "Raw outbound network primitives outside the SSRF-guard seam:\n" + "\n".join(violations)
    )


def test_guarded_adapters_actually_use_safe_urlopen() -> None:
    # Not tautological: the shipped outbound adapters must import the guard.
    users = []
    for rel in (
        "infrastructure/adapters/bsi_validation_service.py",
        "infrastructure/adapters/http_bcf_api_client.py",
        "infrastructure/adapters/kimi_k3_advisory_client.py",
        "infrastructure/security/oidc_token_validator.py",
    ):
        text = (_SRC / rel).read_text(encoding="utf-8")
        if "safe_urlopen" in text:
            users.append(rel)
    assert len(users) == 4, f"expected 4 guarded outbound adapters, found: {users}"
