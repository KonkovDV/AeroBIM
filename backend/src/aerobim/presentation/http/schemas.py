"""Pydantic request schemas for the HTTP API (extracted from api.py)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ValidateIfcRequest(BaseModel):
    request_id: str | None = None
    ifc_path: str = Field(max_length=2048)
    requirement_text: str = Field(default="", max_length=50_000)
    requirement_path: str | None = Field(default=None, max_length=2048)
    ids_path: str | None = Field(default=None, max_length=2048)
    project_name: str | None = Field(default=None, max_length=256)
    discipline: str | None = Field(default=None, max_length=128)
    stage: str | None = Field(default=None, max_length=64)
    information_container_id: str | None = Field(default=None, max_length=256)
    revision: str | None = Field(default=None, max_length=64)
    doc_status: Literal["WIP", "Shared", "Published", "Archived"] | None = None


class DrawingPayload(BaseModel):
    text: str = Field(default="", max_length=50_000)
    path: str | None = Field(default=None, max_length=2048)
    sheet_id: str | None = Field(default=None, max_length=128)
    format: str | None = Field(default=None, max_length=32)


class AnalyzeProjectPackageRequest(BaseModel):
    request_id: str | None = None
    ifc_path: str = Field(max_length=2048)
    requirement_text: str = Field(default="", max_length=50_000)
    requirement_path: str | None = Field(default=None, max_length=2048)
    ids_path: str | None = Field(default=None, max_length=2048)
    technical_spec_text: str = Field(default="", max_length=50_000)
    technical_spec_path: str | None = Field(default=None, max_length=2048)
    calculation_text: str = Field(default="", max_length=50_000)
    calculation_path: str | None = Field(default=None, max_length=2048)
    drawings: list[DrawingPayload] = Field(default_factory=list, max_length=64)
    norm_rule_pack_paths: list[str] = Field(default_factory=list, max_length=16)
    pd_section_path: str | None = Field(default=None, max_length=2048)
    rd_section_path: str | None = Field(default=None, max_length=2048)
    reinforcement_report_path: str | None = Field(default=None, max_length=2048)
    reinforcement_handoff_path: str | None = Field(default=None, max_length=2048)
    reinforcement_source_digest: str | None = Field(default=None, max_length=128)
    reinforcement_waste_warning_threshold_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    reinforcement_provenance_mode: Literal["advisory", "enforced"] = "advisory"
    project_name: str | None = Field(default=None, max_length=256)
    discipline: str | None = Field(default=None, max_length=128)
    stage: str | None = Field(default=None, max_length=64)
    information_container_id: str | None = Field(default=None, max_length=256)
    revision: str | None = Field(default=None, max_length=64)
    doc_status: Literal["WIP", "Shared", "Published", "Archived"] | None = None
    tenant_id: str | None = Field(default=None, max_length=128)
    project_id: str | None = Field(default=None, max_length=256)


class OpenRebarDigestRequest(BaseModel):
    reinforcement_report_path: str = Field(max_length=2048)


class PushBcfApiRequest(BaseModel):
    project_id: str | None = Field(
        default=None,
        max_length=128,
        description="BCF API project id; defaults to AEROBIM_BCF_API_PROJECT_ID",
    )


class ReviewEventRequest(BaseModel):
    event_type: Literal[
        "opened",
        "accepted",
        "rejected",
        "edited_remark",
        "edited",
        "triaged",
        "norm_rule_proposed",
        "norm_rule_edited",
        "drawing_region_escalated",
        "escalated",
        "waived",
        "superseded",
    ]
    issue_rule_id: str | None = Field(default=None, max_length=256)
    actor: str | None = Field(default=None, max_length=128)
    note: str | None = Field(default=None, max_length=2000)
    latency_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    previous_state: str | None = Field(default=None, max_length=64)
    finding_id: str | None = Field(default=None, max_length=64)
    idempotency_key: str | None = Field(default=None, max_length=256)


class NormRuleHitlEventRequest(BaseModel):
    event_type: Literal["norm_rule_proposed", "norm_rule_edited"]
    base_pack_path: str = Field(min_length=1, max_length=512)
    rule_diff: dict[str, object]
    proposed_by: str | None = Field(default=None, max_length=128)
    target_approval_status: Literal["synthetic", "draft", "customer_approved"] | None = None
    approval_ref: str | None = Field(default=None, max_length=512)
    report_id: str | None = Field(default=None, max_length=64)
