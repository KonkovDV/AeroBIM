"""
P1-R: AI Output Provenance.

For every AI-generated output (extraction, remark draft, explanation,
document pairing suggestion) store:
  provider, model, model_version, prompt_template_version,
  toolset_version, relevant_config, input_hashes, output_hash,
  timestamp, provenance_id.

AI outputs are always AI_ADVISORY. They cannot set deterministic verdict.
All AI tool calls are: authenticated, authorized, logged, traceable.

Aligned with NIST AI RMF (GOVERN, MAP, MEASURE, MANAGE) and ISO/IEC 42001.
Reduces: auditability risk, AI governance risk.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class AIOutputType(StrEnum):
    """Category of AI-generated output."""

    EXTRACTION_CANDIDATE = "extraction_candidate"  # Candidate property value
    REMARK_DRAFT = "remark_draft"  # Draft remark text
    EXPLANATION = "explanation"  # Finding explanation
    DOC_PAIRING = "doc_pairing"  # Document ↔ IFC match
    CLASSIFICATION = "classification"  # Element / discipline label
    SUMMARY = "summary"  # Advisory summary
    RULE_SUGGESTION = "rule_suggestion"  # Suggested rule (human must approve)
    NORM_SEARCH = "norm_search"  # Norm clause retrieval


class AIRiskLevel(StrEnum):
    """
    Risk classification per NIST AI RMF.
    Higher risk → stricter human oversight required.
    """

    LOW = "low"  # Advisory text, explanation
    MEDIUM = "medium"  # Extraction candidate, pairing
    HIGH = "high"  # Anything that could influence a finding classification


@dataclass
class AIToolCall:
    """
    A single tool call made by an AI agent within AeroBIM.
    All tool calls are allowlisted, authenticated, authorized, and logged.
    No arbitrary SQL / shell / storage access.
    """

    tool_name: str  # From allowlist: get_project, query_ifc, get_element, etc.
    tool_version: str
    input_summary: str  # Non-sensitive summary (not raw prompt)
    tenant_id: str
    project_id: str
    actor_model: str  # Which AI model made this call
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    authorized: bool = True  # Must be explicitly checked
    audit_logged: bool = True

    # Allowlisted tool names — enforced at runtime
    ALLOWED_TOOLS = {
        "get_project",
        "get_document",
        "query_ifc",
        "get_element",
        "get_evidence",
        "get_norm",
        "search_rule",
        "get_finding",
        "get_revision",
        "draft_remark",
        "get_norm_clause",
        "explain_finding",
        "suggest_document_pairing",
    }

    def validate_allowlist(self) -> None:
        if self.tool_name not in self.ALLOWED_TOOLS:
            raise ValueError(
                f"AI tool call '{self.tool_name}' is not in the allowlist. "
                f"Allowed: {sorted(self.ALLOWED_TOOLS)}"
            )


@dataclass
class AIProvenanceRecord:
    """
    Provenance record for a single AI output.

    Stored alongside (not inside) deterministic evidence.
    provenance_id is the stable identifier; full record is in audit log.
    Confidential prompt/output is NOT stored in public artifact.

    Hallucination / unsupported claim rate must be measured externally
    against this record (P1-S evaluation).
    """

    provenance_id: str  # Stable: sha256(input_hashes + output_hash + model_version)
    output_type: AIOutputType
    risk_level: AIRiskLevel
    provider: str  # e.g. "openai", "anthropic", "local-llm"
    model: str  # e.g. "gpt-4o", "claude-3-5-sonnet"
    model_version: str  # Exact version / snapshot
    prompt_template_version: str  # Git ref or semver of prompt template
    toolset_version: str  # AeroBIM tool API version seen by model
    temperature: float | None  # Relevant sampling config
    input_hashes: list[str]  # sha256 of each input passed to model
    output_hash: str  # sha256 of raw model output
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    tenant_id: str = ""
    project_id: str = ""
    finding_id: str | None = None  # If linked to a finding
    evidence_id: str | None = None  # If linked to evidence
    tool_calls: list[AIToolCall] = field(default_factory=list)
    # These are the explicit limitations the model was given
    stated_limitations: list[str] = field(default_factory=list)
    is_ai_advisory: bool = True  # Always True; cannot be flipped

    @staticmethod
    def compute_provenance_id(
        input_hashes: list[str],
        output_hash: str,
        model_version: str,
        prompt_template_version: str,
    ) -> str:
        payload = json.dumps(
            {
                "input_hashes": sorted(input_hashes),
                "output_hash": output_hash,
                "model_version": model_version,
                "prompt_template_version": prompt_template_version,
            },
            sort_keys=True,
        ).encode()
        return hashlib.sha256(payload).hexdigest()[:32]

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_id": self.provenance_id,
            "output_type": self.output_type.value,
            "risk_level": self.risk_level.value,
            "provider": self.provider,
            "model": self.model,
            "model_version": self.model_version,
            "prompt_template_version": self.prompt_template_version,
            "toolset_version": self.toolset_version,
            "temperature": self.temperature,
            "input_hashes": self.input_hashes,
            "output_hash": self.output_hash,
            "timestamp": self.timestamp.isoformat(),
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "finding_id": self.finding_id,
            "evidence_id": self.evidence_id,
            "is_ai_advisory": self.is_ai_advisory,
            "stated_limitations": self.stated_limitations,
            # tool_calls omitted — stored in separate audit log
        }


@dataclass
class AIEvaluationMetrics:
    """
    Evaluation metrics for an AI advisory capability.
    Must be measured on held-out test set, not development fixtures (P1-J).
    Split by corpus type (P1-I): PUBLIC / SYNTHETIC / CUSTOMER.
    """

    capability: str  # e.g. "remark_draft", "doc_pairing"
    corpus_type: str  # "PUBLIC", "SYNTHETIC", "CUSTOMER"
    model_version: str
    eval_date: str  # ISO date
    test_set_hash: str  # sha256 of test manifest (leakage protection)
    n_samples: int

    # Core metrics (all optional until measured)
    factuality_rate: float | None = None  # 0-1
    grounding_rate: float | None = None  # Citations valid
    abstention_rate: float | None = None  # Model said "I don't know"
    hallucination_rate: float | None = None  # Unsupported evidence refs
    unsupported_claim_rate: float | None = None  # Normative statements w/o basis
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    human_agreement_rate: float | None = None  # Double-annotated subset
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "corpus_type": self.corpus_type,
            "model_version": self.model_version,
            "eval_date": self.eval_date,
            "test_set_hash": self.test_set_hash,
            "n_samples": self.n_samples,
            "factuality_rate": self.factuality_rate,
            "grounding_rate": self.grounding_rate,
            "abstention_rate": self.abstention_rate,
            "hallucination_rate": self.hallucination_rate,
            "unsupported_claim_rate": self.unsupported_claim_rate,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "human_agreement_rate": self.human_agreement_rate,
            "notes": self.notes,
        }
