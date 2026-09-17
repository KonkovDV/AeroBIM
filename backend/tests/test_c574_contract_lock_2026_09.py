"""C574 contract lock: producer/consumer round-trips on the working tree.

Synthetic fixtures only. Does not claim demo GO, product accuracy, or a live
Redis/S3/IFC/browser run.
"""

from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from starlette.requests import Request

from aerobim.application.services.analyze_orchestrators import _OVERLAY_GATE_MASK_RULES
from aerobim.application.services.cross_document_contradictions import (
    CrossDocumentContradictionDetector,
)
from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container
from aerobim.core.di.tokens import Tokens
from aerobim.core.security.path_jail import safe_storage_token
from aerobim.domain.check_coverage import coverage_from_report
from aerobim.domain.hybrid.privacy_guard import PrivacyGuard, PrivacyLeakError
from aerobim.domain.models import (
    ComparisonOperator,
    ConflictKind,
    FindingCategory,
    GeneratedRemark,
    ParsedRequirement,
    ReviewEvent,
    Severity,
    SourceKind,
    ToleranceConfig,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.object_acl import (
    LAB_REVIEWER_AUTH_SCHEME,
    LAB_REVIEWER_SUBJECT,
    AuthPrincipal,
    principal_may_append_hitl_event,
)
from aerobim.domain.quantity import parse_quantity
from aerobim.domain.review_event_chain import genesis_previous_hash, review_event_content_hash
from aerobim.domain.review_projection import effective_text_for_issue
from aerobim.domain.run_passport import build_run_passport, passport_trace
from aerobim.infrastructure.adapters.bcf_report_exporter import collect_bcf_topics
from aerobim.infrastructure.adapters.filesystem_review_event_store import (
    FilesystemReviewEventStore,
)
from aerobim.infrastructure.adapters.redis_analyze_project_package_job_store import _CREATE_LUA
from aerobim.presentation.http.context import ApiContext
from aerobim.presentation.http.routes import uploads as uploads_route
from aerobim.tools.evaluate_detection_precision import evaluate_detection_precision


def _detector() -> CrossDocumentContradictionDetector:
    return CrossDocumentContradictionDetector(ToleranceConfig(), Severity.ERROR)


def _req(**kwargs: object) -> ParsedRequirement:
    values: dict[str, object] = {
        "rule_id": "R1",
        "ifc_entity": "IFCWALL",
        "property_set": "Qto_WallBaseQuantities",
        "property_name": "Width",
        "operator": ComparisonOperator.EQUALS,
        "source_kind": SourceKind.STRUCTURED_TEXT,
        "source": "spec.txt",
    }
    values.update(kwargs)
    return ParsedRequirement(**values)  # type: ignore[arg-type]


def _report(*issues: ValidationIssue, traces: tuple = ()) -> ValidationReport:
    return ValidationReport(
        report_id="a" * 32,
        request_id="req",
        ifc_path=Path("m.ifc"),
        created_at="2026-09-16T00:00:00+00:00",
        requirements=(),
        issues=issues,
        summary=ValidationSummary(0, len(issues), 1, 0, False),
        tool_traces=traces,
    )


def _issue(finding_id: str, *, body: str = "machine", rule_id: str = "R1") -> ValidationIssue:
    return ValidationIssue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        message=body,
        category=FindingCategory.IFC_VALIDATION,
        remark=GeneratedRemark(title="t", body=body),
        finding_id=finding_id,
    )


def _http_request() -> Request:
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
            "client": ("testclient", 50000),
            "server": ("test", 80),
        }
    )


class _Logger:
    def info(self, message: str, **context: object) -> None:
        return None

    def warning(self, message: str, **context: object) -> None:
        return None

    def error(self, message: str, **context: object) -> None:
        return None

    def debug(self, message: str, **context: object) -> None:
        return None


def _ctx(**settings_kwargs: object) -> ApiContext:
    storage = Path(tempfile.mkdtemp())
    defaults: dict[str, object] = dict(
        application_name="aerobim-c574",
        environment="development",
        host="127.0.0.1",
        port=8080,
        storage_dir=storage,
        debug=True,
        allow_anonymous_dev=True,
    )
    defaults.update(settings_kwargs)
    settings = Settings(**defaults)  # type: ignore[arg-type]
    container = Container()
    container.register(Tokens.SETTINGS, lambda _: settings)
    container.register(Tokens.LOGGER, lambda _: _Logger())
    container.register(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE, lambda _: object())
    container.register(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE, lambda _: object())
    container.register(Tokens.AUDIT_REPORT_STORE, lambda _: object())
    return ApiContext(container)


class C574QuantityTests(unittest.TestCase):
    def test_milli_force_is_not_mega(self) -> None:
        milli = parse_quantity(1.0, "mN")
        mega = parse_quantity(1.0, "MN")
        self.assertEqual(milli.si_value, 0.001)
        self.assertEqual(mega.si_value, 1_000_000.0)
        self.assertIsNone(parse_quantity(1.0, "Mm").si_value)
        self.assertEqual(parse_quantity(1.0, "mPa").si_value, 0.001)
        self.assertEqual(parse_quantity(1.0, "MPa").si_value, 1_000_000.0)

    def test_metre_foot_conflict_is_symmetric(self) -> None:
        detector = _detector()
        near = detector.values_conflict("0.3053", "m", "1", "ft")
        swapped = detector.values_conflict("1", "ft", "0.3053", "m")
        self.assertEqual(near, swapped)
        self.assertFalse(near)
        far = detector.values_conflict("0.306", "m", "1", "ft")
        self.assertTrue(far)
        self.assertTrue(detector.values_conflict("1", "ft", "0.306", "m"))

    def test_unknown_interval_does_not_mix_raw_and_si(self) -> None:
        detector = _detector()
        mixed = detector.detect(
            [
                _req(
                    expected_value="1",
                    unit="mystery",
                    operator=ComparisonOperator.GREATER_OR_EQUAL,
                    source="a.txt",
                    source_kind=SourceKind.STRUCTURED_TEXT,
                ),
                _req(
                    expected_value="2",
                    unit="m",
                    operator=ComparisonOperator.LESS_OR_EQUAL,
                    source="b.txt",
                    source_kind=SourceKind.CALCULATION,
                ),
            ]
        )
        kinds = {issue.conflict_kind for issue in mixed}
        self.assertNotIn(ConflictKind.HARD_CONFLICT, kinds)
        unknown = detector.detect(
            [
                _req(
                    expected_value="1",
                    unit="mystery",
                    operator=ComparisonOperator.GREATER_OR_EQUAL,
                    source="a.txt",
                ),
                _req(
                    expected_value="2",
                    unit="mystery",
                    operator=ComparisonOperator.LESS_OR_EQUAL,
                    source="b.txt",
                    source_kind=SourceKind.CALCULATION,
                ),
            ]
        )
        self.assertEqual(unknown, [])

    def test_ambiguous_pset_keeps_target_ref(self) -> None:
        detector = _detector()
        different_objects = detector.detect(
            [
                _req(
                    expected_value="REI60",
                    unit=None,
                    property_set="Pset_WallCommon",
                    property_name="FireRating",
                    target_ref="guid-a",
                    source="a.txt",
                ),
                _req(
                    expected_value="REI90",
                    unit=None,
                    property_set="Pset_FireSafety",
                    property_name="FireRating",
                    target_ref="guid-b",
                    source="b.txt",
                    source_kind=SourceKind.CALCULATION,
                ),
            ]
        )
        self.assertEqual(different_objects, [])
        same_object = detector.detect(
            [
                _req(
                    expected_value="REI60",
                    unit=None,
                    property_set="Pset_WallCommon",
                    property_name="FireRating",
                    target_ref="guid-a",
                    source="a.txt",
                ),
                _req(
                    expected_value="REI90",
                    unit=None,
                    property_set="Pset_FireSafety",
                    property_name="FireRating",
                    target_ref="guid-a",
                    source="b.txt",
                    source_kind=SourceKind.CALCULATION,
                ),
            ]
        )
        self.assertTrue(
            any(issue.conflict_kind is ConflictKind.AMBIGUOUS_MAPPING for issue in same_object)
        )


class C574PassportCoverageTests(unittest.TestCase):
    def test_builder_round_trip_keeps_zero_entity_source(self) -> None:
        passport = build_run_passport(
            sources=(
                {"name": "unread.bin", "size_bytes": 12},
                {"name": "model.ifc", "size_bytes": 64},
            )
        )
        self.assertTrue(passport.get("sources"))
        blob = json.dumps(passport_trace(passport), ensure_ascii=False)
        trace = json.loads(blob)
        cov = coverage_from_report(_report(traces=(trace,)))
        ids = [row.source_id for row in cov.rows]
        self.assertIn("unread.bin", ids)
        self.assertIn("model.ifc", ids)
        unread = next(row for row in cov.rows if row.source_id == "unread.bin")
        self.assertTrue(unread.families)


class C574IdentityTests(unittest.TestCase):
    def test_anonymous_cannot_append_expert_hitl(self) -> None:
        anon = AuthPrincipal(subject="anonymous-dev", auth_scheme="anonymous")
        service = AuthPrincipal(subject="api-bearer", is_service_token=True, auth_scheme="bearer")
        reviewer = AuthPrincipal(
            subject=LAB_REVIEWER_SUBJECT,
            roles=frozenset({"reviewer"}),
            auth_scheme=LAB_REVIEWER_AUTH_SCHEME,
        )
        self.assertFalse(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=False,
                require_hitl_reviewer_roles=False,
                principal=anon,
                event_type="accepted",
            )
        )
        self.assertFalse(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=False,
                require_hitl_reviewer_roles=False,
                principal=service,
                event_type="edited_remark",
            )
        )
        self.assertTrue(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=True,
                require_hitl_reviewer_roles=True,
                principal=reviewer,
                event_type="accepted",
            )
        )

    def test_dev_reviewer_bearer_is_not_anonymous(self) -> None:
        ctx = _ctx(dev_reviewer_token="reviewer-secret", api_bearer_token=None)
        principal = ctx.require_bearer_auth(_http_request(), "Bearer reviewer-secret")
        self.assertEqual(principal.subject, LAB_REVIEWER_SUBJECT)
        self.assertFalse(principal.is_service_token)
        self.assertEqual(principal.auth_scheme, LAB_REVIEWER_AUTH_SCHEME)
        anonymous = ctx.require_bearer_auth(_http_request(), None)
        self.assertEqual(anonymous.subject, "anonymous-dev")


class C574StorageTokenTests(unittest.TestCase):
    def test_variable_hex_escape_is_injective_for_auditor_pair(self) -> None:
        left = safe_storage_token("\uff21")
        right = safe_storage_token("\u0ff2" + "1")
        self.assertNotEqual(left, right)
        self.assertTrue(left.endswith(";"))
        self.assertIn(";", right)


class C574JournalResumeTests(unittest.TestCase):
    def test_partial_seq_promotion_resumes_remaining_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemReviewEventStore(Path(tmp), fail_closed=True)
            report_id = "c" * 32
            target = store._path(report_id)
            target.parent.mkdir(parents=True, exist_ok=True)
            previous = genesis_previous_hash()
            events = []
            for index, event_type in enumerate(("opened", "edited_remark", "accepted"), start=1):
                event = ReviewEvent(
                    event_id=f"e{index}",
                    report_id=report_id,
                    event_type=event_type,  # type: ignore[arg-type]
                    created_at=f"2026-09-16T00:00:0{index}+00:00",
                    finding_id="fid-1",
                    issue_rule_id="R1",
                    actor="expert",
                    sequence_number=index,
                    resulting_state=(
                        "opened"
                        if event_type == "opened"
                        else "edited"
                        if event_type == "edited_remark"
                        else "accepted"
                    ),
                    previous_event_hash=previous,
                )
                stamped = replace(
                    event,
                    content_hash=review_event_content_hash(event, previous_event_hash=previous),
                )
                previous = stamped.content_hash or previous
                events.append(stamped)
            target.write_text(
                "\n".join(json.dumps(asdict(event), ensure_ascii=False) for event in events) + "\n",
                encoding="utf-8",
            )
            seq1 = target.parent / f"{target.name}.seq.1"
            seq1.write_text(
                json.dumps(asdict(events[0]), ensure_ascii=False) + "\n", encoding="utf-8"
            )
            listed = store.list_for_report(report_id)
            self.assertEqual(
                [item.event_type for item in listed], ["opened", "edited_remark", "accepted"]
            )
            self.assertFalse(target.exists())
            restarted = FilesystemReviewEventStore(Path(tmp), fail_closed=True)
            again = restarted.list_for_report(report_id)
            self.assertEqual(len(again), 3)


class C574ExportTests(unittest.TestCase):
    def test_rejected_finding_is_absent_and_edited_text_is_used(self) -> None:
        kept = _issue("keep", body="machine-keep")
        dropped = _issue("drop", body="machine-drop")
        events = (
            ReviewEvent(
                event_id="open-keep",
                report_id="a" * 32,
                event_type="opened",
                created_at="2026-09-16T00:00:01+00:00",
                finding_id="keep",
                issue_rule_id="R1",
                resulting_state="opened",
            ),
            ReviewEvent(
                event_id="edit-keep",
                report_id="a" * 32,
                event_type="edited_remark",
                created_at="2026-09-16T00:00:02+00:00",
                finding_id="keep",
                issue_rule_id="R1",
                note="expert rewrite",
                resulting_state="edited",
            ),
            ReviewEvent(
                event_id="open-drop",
                report_id="a" * 32,
                event_type="opened",
                created_at="2026-09-16T00:00:03+00:00",
                finding_id="drop",
                issue_rule_id="R1",
                resulting_state="opened",
            ),
            ReviewEvent(
                event_id="rej-drop",
                report_id="a" * 32,
                event_type="rejected",
                created_at="2026-09-16T00:00:04+00:00",
                finding_id="drop",
                issue_rule_id="R1",
                resulting_state="rejected",
            ),
        )
        topics = collect_bcf_topics(_report(kept, dropped), review_events=events)
        descriptions = " ".join(topic.description for topic in topics)
        self.assertNotIn("machine-drop", descriptions)
        self.assertIn("expert rewrite", descriptions)
        self.assertEqual(effective_text_for_issue(kept, events), "expert rewrite")
        self.assertEqual(len(topics), 1)


class C574PrivacyOverlayMacroTests(unittest.TestCase):
    def test_residual_overflow_is_fail_closed(self) -> None:
        nested: object = "CANARY_DEEP_OVERFLOW_77"
        for _ in range(8):
            nested = {"child": nested}
        guard = PrivacyGuard(tenant_salt="local-deploy-salt")
        with self.assertRaises(PrivacyLeakError) as caught:
            guard.mask_payload(
                {"secret": nested, "keep": "ok"},
                tenant_id="tenant-a",
                rules={"secret": "remove", "keep": "keep"},
            )
        self.assertIn("incomplete", str(caught.exception))

    def test_overlay_gate_keeps_finding_payload(self) -> None:
        self.assertEqual(_OVERLAY_GATE_MASK_RULES.get("findings_json"), "keep")

    def test_macro_f1_zeros_undefined_classes(self) -> None:
        labels = {
            "schema_version": "1.0.0",
            "dataset_id": "c574-macro",
            "dataset_status": "synthetic",
            "scope_reference": "HARNESS-CONTRACT-ONLY-NOT-CUSTOMER-EVIDENCE",
            "adjudication": {
                "method": "consensus",
                "completed_at": "2026-09-16T00:00:00+00:00",
                "adjudicators": [{"id": "fixture", "role": "fixture author"}],
            },
            "cases": [
                {
                    "case_id": "C1",
                    "expected_findings": [
                        {
                            "finding_class": "class-a",
                            "rule_id": "R-A",
                            "target_ref": "t-a",
                            "adjudication_status": "confirmed",
                        },
                        {
                            "finding_class": "class-b",
                            "rule_id": "R-B",
                            "target_ref": "t-b",
                            "adjudication_status": "confirmed",
                        },
                    ],
                }
            ],
        }
        detections = {
            "schema_version": "1.0.0",
            "run_id": "c574-macro-run",
            "cases": [
                {
                    "case_id": "C1",
                    "findings": [
                        {
                            "finding_class": "class-a",
                            "rule_id": "R-A",
                            "target_ref": "t-a",
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            labels_path = Path(tmp) / "labels.json"
            detections_path = Path(tmp) / "detections.json"
            labels_path.write_text(json.dumps(labels), encoding="utf-8")
            detections_path.write_text(json.dumps(detections), encoding="utf-8")
            report = evaluate_detection_precision(labels_path, detections_path)
        self.assertEqual(report["macro"]["f1"], 0.5)
        self.assertEqual(
            report["macro"]["macro_averaging"],
            "unweighted_mean_over_evaluation_classes_zero_if_undefined",
        )
        self.assertEqual(report["micro"]["f1"], 0.666667)
        self.assertFalse(report["precision_claim"]["publishable"])


class C574StaticContractTests(unittest.TestCase):
    def test_upload_put_is_shielded_from_the_first_await(self) -> None:
        source = inspect.getsource(uploads_route)
        self.assertIn("await asyncio.shield(put_task)", source)
        prefix = source.split("put_task = asyncio.ensure_future", 1)[1]
        first_await = prefix.split("await ", 1)[1].split("\n", 1)[0]
        self.assertIn("asyncio.shield(put_task)", first_await)

    def test_redis_create_lua_does_not_steal_dangling_reservation(self) -> None:
        self.assertIn("idempotency_pending", _CREATE_LUA)
        before_setnx = _CREATE_LUA.split("SET", 1)[0]
        self.assertNotIn("DEL", before_setnx)

    def test_width_extractor_is_qto_wall_base_only(self) -> None:
        from aerobim.infrastructure.adapters import ifc_wall_width_extractor as width_mod

        source = inspect.getsource(width_mod)
        self.assertIn("Qto_WallBaseQuantities", source)
        self.assertIn("LENGTHUNIT scale NOT_VERIFIED", source)
        self.assertIn("with open_ifc_session", source)

    def test_open_storage_file_binds_parent_inode(self) -> None:
        from aerobim.core.security import path_jail as path_jail_module

        source = inspect.getsource(path_jail_module.open_storage_file)
        self.assertIn("_posix_open_at_parent", source)
        self.assertIn("_windows_open_nofollow", source)


if __name__ == "__main__":
    unittest.main()
