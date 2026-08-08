"""Red Team Master Audit remediation — August 2026."""

from __future__ import annotations

import concurrent.futures
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

from aerobim.core.security.object_limits import ObjectTooLargeError, read_http_response_capped
from aerobim.core.security.zip_limits import ZipBombError, read_zip_member_capped
from aerobim.domain.models import ReviewEvent
from aerobim.infrastructure.adapters.filesystem_review_event_store import FilesystemReviewEventStore
from aerobim.presentation.http.errors import public_bad_request_detail


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self, n: int = -1) -> bytes:
        if n < 0:
            return self._payload
        return self._payload[:n]


class HttpResponseCapTests(unittest.TestCase):
    def test_caps_oversized_body(self) -> None:
        with self.assertRaises(ObjectTooLargeError):
            read_http_response_capped(_FakeResponse(b"x" * 32), max_bytes=8)

    def test_allows_within_cap(self) -> None:
        raw = read_http_response_capped(_FakeResponse(b"ok"), max_bytes=8)
        self.assertEqual(raw, b"ok")


class ZipMemberCapTests(unittest.TestCase):
    def test_rejects_oversized_declared_member(self) -> None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            archive.writestr("big.txt", b"x" * 2048)
        with zipfile.ZipFile(io.BytesIO(buf.getvalue()), "r") as zf:
            with self.assertRaises(ZipBombError):
                read_zip_member_capped(zf, "big.txt", max_member_bytes=1024)


class HitlConcurrentAppendTests(unittest.TestCase):
    def test_concurrent_appends_get_unique_sequences(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemReviewEventStore(Path(tmp))
            report_id = f"rpt-{uuid4().hex}"

            def _append(index: int) -> str:
                return store.append(
                    ReviewEvent(
                        event_id=f"evt-{index}",
                        report_id=report_id,
                        event_type="opened",
                        created_at="2026-08-08T00:00:00Z",
                    )
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                futures = [pool.submit(_append, i) for i in range(16)]
                event_ids = {future.result() for future in futures}

            self.assertEqual(len(event_ids), 16)
            events = store.list_for_report(report_id)
            sequences = [e.sequence_number for e in events if e.sequence_number is not None]
            self.assertEqual(len(sequences), 16)
            self.assertEqual(len(set(sequences)), 16)


class PublicErrorDetailTests(unittest.TestCase):
    def test_bad_request_detail_is_stable(self) -> None:
        self.assertEqual(public_bad_request_detail(), "Invalid request")
        self.assertNotIn("/", public_bad_request_detail())


class LlmExtractionEgressCapTests(unittest.TestCase):
    def test_live_adapter_caps_response(self) -> None:
        from aerobim.infrastructure.adapters.llm_extraction_adapters import (
            OpenAICompatLlmExtractionAdapter,
        )

        oversized = b"x" * (1024 * 1024 + 64)
        adapter = OpenAICompatLlmExtractionAdapter(
            provider="kimi",
            base_url="https://kimi.example.com/v1",
            api_key="k",
            live=True,
            allowed_hosts=frozenset({"kimi.example.com"}),
        )

        def _fake_urlopen(request, *, timeout, allow_http=False):  # noqa: ANN001
            return MagicMock(
                __enter__=lambda s: s,
                __exit__=lambda *a: None,
                read=lambda n=-1: oversized[: n if n > 0 else len(oversized)],
            )

        import aerobim.core.security.outbound_url as outbound_url

        with unittest.mock.patch.object(outbound_url, "safe_urlopen", _fake_urlopen):
            result = adapter.extract_candidates("hello", source_id="s1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, "failed")


if __name__ == "__main__":
    unittest.main()
