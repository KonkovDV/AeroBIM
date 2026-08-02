"""JSON detached signature envelope auditor (WP-03 foundation).

Loads ``*.sig.json`` next to the content file (or an explicit envelope path),
hashes content bytes read-only, and assesses the envelope via domain rules.
Never rewrites original content bytes. Never claims УКЭП legal validity —
``trust_chain_status`` stays ``not_verified``.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from aerobim.domain.signature_immutability import (
    SignatureAuditResult,
    SignatureEnvelope,
    assess_signature_envelope,
    content_sha256_hex,
    missing_envelope_result,
)


class JsonDetachedSignatureAuditor:
    """Filesystem JSON adapter for ``DocumentSignatureAuditor``."""

    def audit(
        self,
        content_path: Path,
        *,
        envelope_path: Path | None = None,
        required_roles: Sequence[str] = (),
    ) -> SignatureAuditResult:
        resolved_envelope = (
            envelope_path
            if envelope_path is not None
            else content_path.with_suffix(content_path.suffix + ".sig.json")
        )
        if not resolved_envelope.is_file():
            return missing_envelope_result(reason="missing_envelope")

        try:
            payload = json.loads(resolved_envelope.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return SignatureAuditResult(
                structure_ok=False,
                integrity_ok=False,
                roles_complete=False,
                validity_window_ok=None,
                trust_chain_status="not_verified",
                overall_status="failed",
                claim_boundary=missing_envelope_result().claim_boundary,
                reasons=(f"envelope_unreadable:{exc}", "trust_chain_not_verified"),
            )

        if not isinstance(payload, dict):
            return SignatureAuditResult(
                structure_ok=False,
                integrity_ok=False,
                roles_complete=False,
                validity_window_ok=None,
                trust_chain_status="not_verified",
                overall_status="failed",
                claim_boundary=missing_envelope_result().claim_boundary,
                reasons=("envelope_not_object", "trust_chain_not_verified"),
            )

        # Read-only hash of original content — never rewrite content bytes.
        digest = content_sha256_hex(content_path)
        envelope = SignatureEnvelope.from_mapping(payload)
        return assess_signature_envelope(
            envelope,
            digest,
            required_roles,
            signing_time=envelope.signing_time,
        )
