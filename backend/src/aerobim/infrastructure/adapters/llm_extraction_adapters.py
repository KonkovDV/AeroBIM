"""Advisory LLM extraction adapters (regex baseline + OpenAI-compat kimi/qwen).

Never wired into AnalyzeProjectPackageUseCase verdict path.
"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request

from aerobim.core.config.settings import (
    _DEFAULT_LLM_ALLOWED_HOSTS,
    assert_llm_base_host_allowed,
)
from aerobim.core.security.object_limits import read_http_response_capped
from aerobim.core.security.outbound_url import safe_urlopen
from aerobim.domain.llm_extraction import ExtractionCandidate
from aerobim.domain.models import RequirementSource, SourceKind
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer

_EXTRACTION_SYSTEM = (
    "You extract IFC-oriented requirements from AEC text. "
    'Return JSON object {"candidates":[...]} only. '
    "Each candidate needs ifc_entity, property_set, property_name, expected_value, "
    "evidence_refs (non-empty quote spans from the source). "
    "Never invent values without an evidence_ref quote."
)


class RegexRequirementExtractionAdapter:
    """Deterministic baseline: pipe rows + RU narrative patterns."""

    def __init__(self) -> None:
        self._structured = StructuredRequirementExtractor()
        self._narrative = NarrativeRuleSynthesizer()

    def extract_candidates(
        self, text: str, *, source_id: str | None = None
    ) -> list[ExtractionCandidate]:
        source = RequirementSource(
            text=text,
            source_kind=SourceKind.STRUCTURED_TEXT,
            source_id=source_id or "regex-extraction",
        )
        candidates: list[ExtractionCandidate] = []
        try:
            parsed = self._structured.extract(source)
        except ValueError:
            parsed = []
        if not parsed:
            parsed = self._narrative.synthesize(source)
        for item in parsed:
            evidence = item.evidence_text or text[:200]
            candidates.append(
                ExtractionCandidate(
                    rule_id=item.rule_id,
                    ifc_entity=item.ifc_entity,
                    property_set=item.property_set,
                    property_name=item.property_name,
                    expected_value=item.expected_value,
                    evidence_refs=(evidence,),
                    confidence=item.confidence,
                    provider="regex",
                    status="ok",
                    unit=item.unit,
                    operator=item.operator.value if item.operator else None,
                )
            )
        return candidates


class OpenAICompatLlmExtractionAdapter:
    """OpenAI-compat extraction for kimi|qwen labels; fail-closed when unconfigured."""

    def __init__(
        self,
        *,
        provider: str,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str = "mock",
        timeout_seconds: float = 30.0,
        allowed_hosts: frozenset[str] | None = None,
        live: bool = False,
    ) -> None:
        self._provider = provider.strip().lower() or "unknown"
        self._base_url = (base_url or "").rstrip("/")
        self._api_key = api_key or ""
        self._model = model
        self._timeout = timeout_seconds
        self._allowed_hosts = frozenset(allowed_hosts or _DEFAULT_LLM_ALLOWED_HOSTS)
        self._live = live and bool(self._base_url) and bool(self._api_key)

    def extract_candidates(
        self, text: str, *, source_id: str | None = None
    ) -> list[ExtractionCandidate]:
        if not self._live:
            return [
                ExtractionCandidate(
                    rule_id=None,
                    ifc_entity=None,
                    property_set=None,
                    property_name=None,
                    expected_value=None,
                    evidence_refs=(),
                    provider=self._provider,
                    status="skipped",
                )
            ]
        try:
            assert_llm_base_host_allowed(self._base_url, self._allowed_hosts)
            payload = self._chat(text)
            return self._parse_payload(payload, source_id=source_id)
        except (HTTPError, URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError):
            return [
                ExtractionCandidate(
                    rule_id=None,
                    ifc_entity=None,
                    property_set=None,
                    property_name=None,
                    expected_value=None,
                    evidence_refs=(),
                    provider=self._provider,
                    status="failed",
                )
            ]

    def _chat(self, text: str) -> dict[str, Any]:
        url = f"{self._base_url}/chat/completions"
        body = {
            "model": self._model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _EXTRACTION_SYSTEM},
                {
                    "role": "user",
                    "content": f"source_text:\n{text[:8000]}",
                },
            ],
        }
        request = Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        with safe_urlopen(request, timeout=self._timeout) as response:
            raw = read_http_response_capped(response).decode("utf-8")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response must be object")
        return parsed

    def _parse_payload(
        self, payload: dict[str, Any], *, source_id: str | None
    ) -> list[ExtractionCandidate]:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("missing choices")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise ValueError("missing content")
        # Strip optional markdown fences
        cleaned = content.strip()
        fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.S)
        if fence:
            cleaned = fence.group(1)
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("content JSON must be object")
        raw_candidates = data.get("candidates")
        if not isinstance(raw_candidates, list):
            raise ValueError("candidates must be list")
        out: list[ExtractionCandidate] = []
        for index, item in enumerate(raw_candidates):
            if not isinstance(item, dict):
                continue
            refs_raw = item.get("evidence_refs") or []
            refs = (
                tuple(str(r) for r in refs_raw if str(r).strip())
                if isinstance(refs_raw, list)
                else ()
            )
            out.append(
                ExtractionCandidate(
                    rule_id=str(item["rule_id"])
                    if item.get("rule_id")
                    else f"{source_id or 'llm'}-{index}",
                    ifc_entity=str(item["ifc_entity"]).upper() if item.get("ifc_entity") else None,
                    property_set=str(item["property_set"]) if item.get("property_set") else None,
                    property_name=str(item["property_name"]) if item.get("property_name") else None,
                    expected_value=str(item["expected_value"])
                    if item.get("expected_value") is not None
                    else None,
                    evidence_refs=refs,
                    confidence=float(item["confidence"])
                    if isinstance(item.get("confidence"), (int, float))
                    else None,
                    provider=self._provider,
                    status="ok",
                    unit=str(item["unit"]) if item.get("unit") else None,
                    operator=str(item["operator"]) if item.get("operator") else None,
                )
            )
        return out


__all__ = [
    "OpenAICompatLlmExtractionAdapter",
    "RegexRequirementExtractionAdapter",
]
