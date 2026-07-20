"""Apply HITL norm-rule proposals as immutable pack versions (P0.3)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from aerobim.domain.models import NormApprovalStatus, NormPackVersionInfo, ReviewEvent
from aerobim.domain.norm_pack_hash import compute_norm_pack_content_hash
from aerobim.domain.ports import NormRulePackVersionStore, ReviewEventStore

NormRuleHitlEventType = Literal["norm_rule_proposed", "norm_rule_edited"]


class ApplyNormRuleHitlEventUseCase:
    """Create a new pack version from a HITL rule proposal/edit.

    Never mutates prior ObjectStore keys. Promotion to ``customer_approved``
    requires a non-empty ``approval_ref`` — we do not invent customer packs.
    """

    def __init__(
        self,
        *,
        version_store: NormRulePackVersionStore,
        review_event_store: ReviewEventStore,
    ) -> None:
        self._versions = version_store
        self._events = review_event_store

    def execute(
        self,
        *,
        pack_id: str,
        base_pack_path: Path,
        event_type: NormRuleHitlEventType,
        rule_diff: dict[str, object],
        proposed_by: str | None,
        target_approval_status: NormApprovalStatus | None = None,
        approval_ref: str | None = None,
        report_id: str | None = None,
        tenant_id: str | None = None,
    ) -> tuple[NormPackVersionInfo, ReviewEvent]:
        if not isinstance(rule_diff, dict) or not rule_diff.get("rule_id"):
            raise ValueError("rule_diff must be an object with rule_id")

        status = target_approval_status or "draft"
        if status == "customer_approved" and not (approval_ref or "").strip():
            raise ValueError("customer_approved HITL upgrades require a non-empty approval_ref")

        bound_tenant = (tenant_id or "").strip() or None

        base_bytes = base_pack_path.read_bytes()
        try:
            payload = json.loads(base_bytes.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Base norm pack is not valid JSON: {base_pack_path}") from exc
        if not isinstance(payload, dict):
            raise ValueError("Base norm pack root must be a JSON object")
        if str(payload.get("pack_id", "")) != pack_id:
            raise ValueError(f"pack_id mismatch: event={pack_id!r} base={payload.get('pack_id')!r}")

        parent_version = str(payload.get("version") or "0.0.0")
        existing = self._versions.list_versions(pack_id, tenant_id=bound_tenant)
        next_index = len(existing) + 1
        new_version = f"{parent_version}+hitl.{next_index}"

        rules = payload.get("rules")
        if not isinstance(rules, list):
            raise ValueError("Base norm pack rules must be an array")
        rule_id = str(rule_diff["rule_id"])
        replaced = False
        updated_rules: list[object] = []
        for item in rules:
            if isinstance(item, dict) and str(item.get("rule_id")) == rule_id:
                merged = dict(item)
                merged.update(rule_diff)
                updated_rules.append(merged)
                replaced = True
            else:
                updated_rules.append(item)
        if not replaced:
            updated_rules.append(dict(rule_diff))

        payload["rules"] = updated_rules
        payload["version"] = new_version
        labels = payload.get("claim_labels")
        if isinstance(labels, list):
            synthetic = {
                str(item).strip().lower()
                for item in labels
                if isinstance(item, str) and item.strip()
            }
        else:
            synthetic = set()
        if status == "customer_approved":
            if synthetic.intersection(
                {"synthetic", "fixture", "template", "not-customer-evidence"}
            ):
                raise ValueError(
                    "synthetic/fixture claim_labels cannot promote to customer_approved "
                    "(RT-002 open)"
                )
            # Residential reference template defaults to synthetic labels when absent.
            if not labels and str(payload.get("status", "")).startswith("synthetic"):
                raise ValueError(
                    "synthetic base packs cannot promote to customer_approved (RT-002 open)"
                )
            now = datetime.now(tz=UTC).isoformat()
            payload["status"] = "customer_approved"
            payload["approval_ref"] = approval_ref
            if not payload.get("jurisdiction"):
                raise ValueError(
                    "customer_approved HITL upgrades require pack jurisdiction metadata"
                )
            rules_for_hash = payload.get("rules")
            if isinstance(rules_for_hash, list):
                for item in rules_for_hash:
                    if not isinstance(item, dict):
                        continue
                    clause = item.get("norm_clause") or item.get("clause")
                    if not (isinstance(clause, str) and clause.strip()):
                        raise ValueError(
                            "customer_approved HITL upgrades require clause/norm_clause "
                            f"on every rule (missing on {item.get('rule_id')!r})"
                        )

            payload["approval"] = {
                "approved_by": proposed_by or "hitl-engineer",
                "approval_date": now,
                "approval_status": "customer_approved",
                "document_title": str(payload.get("title") or pack_id),
                "document_edition": str(payload.get("edition") or payload.get("version") or "1"),
                "effective_date": now[:10],
                "scope_reference": approval_ref,
            }
            payload["pack_hash"] = compute_norm_pack_content_hash(payload)
            # Strip synthetic honesty labels before customer storage.
            payload["claim_labels"] = ["customer-evidence"]
        elif status == "draft":
            payload["status"] = "draft"
            payload["approval"] = None
            merged = [*(labels if isinstance(labels, list) else []), "draft"]
            payload["claim_labels"] = list(dict.fromkeys(merged))
        else:
            payload["status"] = "synthetic-template"
            payload["approval"] = None
            merged = [
                *(labels if isinstance(labels, list) else []),
                "synthetic",
                "not-customer-evidence",
            ]
            payload["claim_labels"] = list(dict.fromkeys(merged))

        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        record = self._versions.save_version(
            pack_id=pack_id,
            version=new_version,
            payload=encoded,
            created_by=proposed_by,
            parent_version=parent_version,
            approval_status=status,
            approval_ref=approval_ref,
            tenant_id=bound_tenant,
        )

        event = ReviewEvent(
            event_id=uuid4().hex,
            report_id=report_id or f"pack:{pack_id}",
            event_type=event_type,
            created_at=datetime.now(tz=UTC).isoformat(),
            actor=proposed_by,
            note=f"HITL pack version {new_version} from {parent_version}",
            pack_id=pack_id,
            resulting_pack_version=new_version,
            target_approval_status=status,
            approval_ref=approval_ref,
            rule_diff_json=json.dumps(rule_diff, ensure_ascii=False),
        )
        self._events.append(event)
        return record, event
