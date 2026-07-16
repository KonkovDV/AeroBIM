"""Optional client for buildingSMART IFC Validation Service API.

API preview (dev): ``POST /api/v1/validationrequest`` with Token auth returns
``public_id`` used as the stored certificate / request reference.
See: https://buildingsmart.github.io/validate/dev/
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any
from urllib import error, request


class HttpBsiValidationService:
    """Submits IFC files to a bSI Validation Service compatible endpoint."""

    def __init__(
        self,
        *,
        base_url: str,
        api_token: str,
        timeout_seconds: float = 60.0,
        http_submit: Any | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._timeout_seconds = timeout_seconds
        self._http_submit = http_submit or self._default_submit

    def submit(self, ifc_path: Path) -> str:
        if not ifc_path.is_file():
            raise FileNotFoundError(ifc_path)
        payload = ifc_path.read_bytes()
        response = self._http_submit(
            f"{self._base_url}/api/v1/validationrequest",
            ifc_path.name,
            payload,
            self._api_token,
            self._timeout_seconds,
        )
        public_id = response.get("public_id") or response.get("id")
        if public_id is None:
            raise RuntimeError(f"bSI Validation Service response missing public_id: {response}")
        return str(public_id)

    @staticmethod
    def _default_submit(
        url: str,
        file_name: str,
        payload: bytes,
        api_token: str,
        timeout_seconds: float,
    ) -> dict[str, object]:
        boundary = f"----aerobim{uuid.uuid4().hex}"
        body = (
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file_name"\r\n\r\n'
                f"{file_name}\r\n"
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode()
            + payload
            + f"\r\n--{boundary}--\r\n".encode()
        )
        req = request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Token {api_token}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Accept": "application/json",
            },
        )
        try:
            with request.urlopen(req, timeout=timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                parsed = json.loads(raw) if raw.strip() else {}
                return parsed if isinstance(parsed, dict) else {}
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"bSI Validation Service HTTP {exc.code}: {detail}") from exc


class LocalSchemaPackCertificate:
    """Offline stand-in: records a deterministic local schema-pack certificate id."""

    def __init__(self, *, pack_id: str = "aerobim-local-spf-pregate-v1") -> None:
        self._pack_id = pack_id

    def submit(self, ifc_path: Path) -> str:
        if not ifc_path.is_file():
            raise FileNotFoundError(ifc_path)
        digest = ifc_path.stat().st_size
        return f"{self._pack_id}:{ifc_path.name}:{digest}"
