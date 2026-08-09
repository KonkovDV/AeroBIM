"""Red Team Wave 3 remediation — August 2026."""

from __future__ import annotations

import concurrent.futures
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from aerobim.core.security.path_jail import sanitize_upload_filename
from aerobim.domain.object_acl import AuthPrincipal, principal_may_append_hitl_event
from aerobim.domain.review_event_append import ReviewEventAppendSpec
from aerobim.domain.review_event_chain import review_event_content_hash
from aerobim.infrastructure.adapters.filesystem_review_event_store import (
    FilesystemReviewEventStore,
)
from aerobim.presentation.http.context import attachment_content_disposition
from aerobim.presentation.http.errors import public_upload_quota_exceeded_detail


class HitlLockedAppendTests(unittest.TestCase):
    def test_concurrent_api_appends_get_unique_sequences_and_hash_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemReviewEventStore(Path(tmp))
            report_id = f"rpt-{uuid4().hex}"

            def _append(index: int) -> str:
                event = store.append_api_event(
                    ReviewEventAppendSpec(
                        report_id=report_id,
                        event_type="escalated",
                        created_at=f"2026-08-08T00:00:{index:02d}Z",
                        actor="system",
                        note=f"auto-{index}",
                        finding_id=f"finding-{index}",
                        idempotency_key=f"idem-{index}",
                        event_id=f"evt-{index:02d}",
                    )
                )
                return event.event_id

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                event_ids = {pool.submit(_append, i).result() for i in range(12)}

            self.assertEqual(len(event_ids), 12)
            events = store.list_for_report(report_id)
            sequences = [e.sequence_number for e in events]
            self.assertEqual(len(set(sequences)), 12)
            hashes = [e.content_hash for e in events]
            self.assertTrue(all(hashes))
            for idx, event in enumerate(events, start=1):
                if idx == 1:
                    continue
                prior = events[idx - 2]
                self.assertEqual(event.previous_event_hash, prior.content_hash)
                recomputed = review_event_content_hash(
                    event,
                    previous_event_hash=event.previous_event_hash or "",
                )
                self.assertEqual(recomputed, event.content_hash)


class HitlRbacTests(unittest.TestCase):
    def test_static_bearer_blocked_from_expert_events_in_production_profile(self) -> None:
        class _Settings:
            signoff_profile = "production"

            @property
            def enforce_hitl_reviewer_auth(self) -> bool:
                return self.signoff_profile in {"samolet_pilot", "production"}

        principal = AuthPrincipal(tenant_id="t1", subject="api-bearer", is_service_token=True)
        settings = _Settings()
        self.assertFalse(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=settings.enforce_hitl_reviewer_auth,
                require_hitl_reviewer_roles=True,
                principal=principal,
                event_type="accepted",
            )
        )
        self.assertTrue(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=settings.enforce_hitl_reviewer_auth,
                require_hitl_reviewer_roles=True,
                principal=AuthPrincipal(
                    tenant_id="t1", subject="oidc-user", roles=frozenset({"reviewer"})
                ),
                event_type="accepted",
            )
        )

    def test_static_bearer_blocked_even_when_role_gate_disabled(self) -> None:
        """N-32: shared bearer never signs — including development / non-pilot profiles."""

        principal = AuthPrincipal(tenant_id="t1", subject="api-bearer", is_service_token=True)
        self.assertFalse(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=False,
                require_hitl_reviewer_roles=False,
                principal=principal,
                event_type="accepted",
            )
        )
        self.assertFalse(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=False,
                require_hitl_reviewer_roles=False,
                principal=principal,
                event_type="rejected",
            )
        )
        self.assertTrue(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=False,
                require_hitl_reviewer_roles=False,
                principal=AuthPrincipal(tenant_id="t1", subject="local-expert"),
                event_type="accepted",
            )
        )
        self.assertTrue(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=False,
                require_hitl_reviewer_roles=False,
                principal=principal,
                event_type="opened",
            )
        )

    def test_hitl_role_gate_profile_matrix(self) -> None:
        """N-49: reviewer roles required only under pilot/production; demo/default off."""

        from types import SimpleNamespace

        from aerobim.core.config.settings import Settings

        reviewer = AuthPrincipal(
            tenant_id="t1",
            subject="oidc-user",
            roles=frozenset({"reviewer"}),
        )
        no_role = AuthPrincipal(tenant_id="t1", subject="oidc-user", roles=frozenset())

        for profile, roles_required in (
            ("samolet_pilot", True),
            ("production", True),
            ("development", False),
            ("fixture", False),
        ):
            probe = SimpleNamespace(signoff_profile=profile)
            enforce = Settings.enforce_hitl_reviewer_auth.__get__(probe, Settings)
            require_roles = Settings.require_hitl_reviewer_roles.__get__(probe, Settings)
            self.assertEqual(enforce, roles_required, msg=f"enforce flag for {profile}")
            self.assertEqual(require_roles, roles_required, msg=f"require roles for {profile}")
            self.assertTrue(
                principal_may_append_hitl_event(
                    enforce_hitl_reviewer_auth=enforce,
                    require_hitl_reviewer_roles=require_roles,
                    principal=reviewer,
                    event_type="accepted",
                ),
                msg=f"reviewer may accept under {profile}",
            )
            may_no_role = principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=enforce,
                require_hitl_reviewer_roles=require_roles,
                principal=no_role,
                event_type="accepted",
            )
            self.assertEqual(
                may_no_role,
                not roles_required,
                msg=f"no-role principal under {profile}",
            )


class UploadFilenameTests(unittest.TestCase):
    def test_sanitize_strips_control_chars_and_reserved_names(self) -> None:
        name = sanitize_upload_filename("CON.pdf")
        self.assertTrue(name.startswith("_"))
        rtl = sanitize_upload_filename("evi\u202egnp.exe")
        self.assertNotIn("\u202e", rtl)


class ContentDispositionTests(unittest.TestCase):
    def test_utf8_filename_star_present_for_non_ascii(self) -> None:
        header = attachment_content_disposition("отчёт.pdf")
        self.assertIn("filename*=", header)
        self.assertIn("UTF-8", header)


class StableUploadErrorTests(unittest.TestCase):
    def test_quota_detail_is_stable(self) -> None:
        self.assertEqual(public_upload_quota_exceeded_detail(), "Upload quota exceeded")


if __name__ == "__main__":
    unittest.main()
