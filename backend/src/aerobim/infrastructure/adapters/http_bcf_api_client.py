"""HTTP client for buildingSMART BCF API 3.0 topic push (OpenCDE family).

Auth follows OpenCDE Foundation conventions: ``Authorization: Bearer <access_token>``
obtained out-of-band (authorization_code / password grant / hub-issued token).
This adapter does not implement the interactive OAuth dance — operators supply a
pre-issued access token via settings or request override.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from aerobim.domain.bcf_api import BcfApiPushResult, BcfApiTopicPushResult
from aerobim.domain.models import ValidationReport
from aerobim.infrastructure.adapters.bcf_report_exporter import collect_bcf_topics


class HttpBcfApiClient:
    """Infrastructure adapter implementing ``BcfApiClient``."""

    def __init__(
        self,
        *,
        base_url: str,
        access_token: str,
        api_version: str = "3.0",
        timeout_seconds: float = 30.0,
        http_post: Any | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._access_token = access_token
        self._api_version = api_version.strip() or "3.0"
        self._timeout_seconds = timeout_seconds
        self._http_post = http_post or self._default_http_post

    def push_report_topics(
        self,
        report: ValidationReport,
        *,
        project_id: str,
    ) -> BcfApiPushResult:
        if not project_id.strip():
            raise ValueError("BCF API project_id is required")
        import re

        if not re.fullmatch(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            project_id.strip(),
        ):
            raise ValueError("BCF API project_id must be a UUID")
        if not self._access_token.strip():
            raise ValueError("BCF API access token is required")

        results: list[BcfApiTopicPushResult] = []
        for topic in collect_bcf_topics(report):
            body: dict[str, object] = {
                "guid": topic.topic_guid,
                "title": topic.title,
                "description": topic.description,
                "topic_type": topic.topic_type,
                "topic_status": topic.topic_status.lower() if topic.topic_status else "open",
                "reference_links": list(topic.reference_links),
            }
            try:
                response = self._http_post(
                    self._topics_url(project_id),
                    body,
                    self._access_token,
                    self._timeout_seconds,
                )
                results.append(
                    BcfApiTopicPushResult(
                        title=topic.title,
                        remote_guid=str(response.get("guid") or topic.topic_guid),
                        server_assigned_id=(
                            str(response["server_assigned_id"])
                            if response.get("server_assigned_id") is not None
                            else None
                        ),
                        success=True,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                results.append(
                    BcfApiTopicPushResult(
                        title=topic.title,
                        remote_guid=None,
                        server_assigned_id=None,
                        success=False,
                        error_message=str(exc),
                    )
                )

        succeeded = sum(1 for item in results if item.success)
        failed = len(results) - succeeded
        return BcfApiPushResult(
            project_id=project_id,
            attempted=len(results),
            succeeded=succeeded,
            failed=failed,
            topics=tuple(results),
        )

    def _topics_url(self, project_id: str) -> str:
        return f"{self._base_url}/bcf/{self._api_version}/projects/{project_id}/topics"

    @staticmethod
    def _default_http_post(
        url: str,
        body: dict[str, object],
        access_token: str,
        timeout_seconds: float,
    ) -> dict[str, object]:
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            from aerobim.core.security.outbound_url import safe_urlopen

            with safe_urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                if not raw.strip():
                    return {}
                parsed = json.loads(raw)
                return parsed if isinstance(parsed, dict) else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"BCF API HTTP {exc.code}: {detail}") from exc
