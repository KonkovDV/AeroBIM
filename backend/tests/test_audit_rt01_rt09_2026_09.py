"""RT01–RT09 counterexamples on the current working tree. Synthetic only."""

from __future__ import annotations

import csv
import inspect
import os
import tempfile
import unittest
from pathlib import Path

from aerobim.application.services.determinism_gate import DeterminismGate, build_evidence_universe
from aerobim.core.security.outbound_url import (
    clear_outbound_dial_pins,
    ensure_outbound_dial_pins_installed,
    rewrite_dial_address,
    set_outbound_dial_pin,
)
from aerobim.core.security.path_jail import (
    PathJailError,
    _assert_fd_still_is_path,
    _windows_path_is_under_base,
    open_storage_file,
    safe_storage_token,
    tenant_storage_prefix,
)
from aerobim.domain.architecture import PrecisionClaim, precision_claim_publishable_with_agreement
from aerobim.domain.hybrid.privacy_guard import PrivacyGuard, PrivacyLeakError
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue
from aerobim.presentation.http.context import _oidc_tenant_from_claim
from aerobim.tools.evaluate_detection_precision import MetricCounts
from aerobim.tools.measure_adjudicator_agreement import measure_adjudication_csv


class RT01Urllib3DialPinTests(unittest.TestCase):
    def tearDown(self) -> None:
        clear_outbound_dial_pins()

    def test_rewrite_uses_pinned_ip_not_hostname(self) -> None:
        ensure_outbound_dial_pins_installed()
        set_outbound_dial_pin("pin-probe.invalid", "203.0.113.77")
        self.assertEqual(
            rewrite_dial_address(("pin-probe.invalid", 443)),
            ("203.0.113.77", 443),
        )
        self.assertEqual(
            rewrite_dial_address(("other.test.invalid", 443)),
            ("other.test.invalid", 443),
        )

    def test_urllib3_module_is_wrapped_when_present(self) -> None:
        try:
            import urllib3.util.connection as urllib3_connection
        except ImportError:
            self.skipTest("urllib3 not installed")
        ensure_outbound_dial_pins_installed()
        self.assertTrue(
            getattr(urllib3_connection.create_connection, "_aerobim_outbound_pin", False)
        )

    def test_urllib3_connection_module_is_wrapped_when_present(self) -> None:
        try:
            import urllib3.connection as urllib3_http
        except ImportError:
            self.skipTest("urllib3.connection not installed")
        ensure_outbound_dial_pins_installed()
        bound = getattr(urllib3_http, "create_connection", None)
        if bound is None:
            self.skipTest("urllib3.connection.create_connection is not a module attribute")
        self.assertTrue(getattr(bound, "_aerobim_outbound_pin", False))

    def test_urllib3_httpconnection_new_conn_is_wrapped_when_present(self) -> None:
        try:
            import urllib3.connection as urllib3_http
        except ImportError:
            self.skipTest("urllib3.connection not installed")
        ensure_outbound_dial_pins_installed()
        http_conn = getattr(urllib3_http, "HTTPConnection", None)
        orig_new = getattr(http_conn, "_new_conn", None) if http_conn is not None else None
        if orig_new is None:
            self.skipTest("urllib3 HTTPConnection._new_conn is not present")
        self.assertTrue(getattr(orig_new, "_aerobim_outbound_pin", False))


class RT02TenantIdentityTests(unittest.TestCase):
    def test_fullwidth_and_ascii_tenants_do_not_share_prefix(self) -> None:
        wide = tenant_storage_prefix("\uff21enant")
        ascii_ = tenant_storage_prefix("Aenant")
        self.assertNotEqual(wide, ascii_)
        self.assertNotEqual(safe_storage_token("\uff21enant"), safe_storage_token("Aenant"))
        claim_wide = _oidc_tenant_from_claim("\uff21enant")
        claim_ascii = _oidc_tenant_from_claim("Aenant")
        self.assertNotEqual(claim_wide, claim_ascii)
        self.assertNotEqual(tenant_storage_prefix(claim_wide), tenant_storage_prefix(claim_ascii))


class RT03GroundingNameTests(unittest.TestCase):
    def test_known_guid_wrong_value_is_not_claim_supported(self) -> None:
        gate = DeterminismGate()
        universe = build_evidence_universe(
            engine_issues=(
                ValidationIssue(
                    rule_id="IDS-1",
                    severity=Severity.ERROR,
                    message="engine 200 mm",
                    category=FindingCategory.IDS_VALIDATION,
                    element_guid="guid-known",
                    observed_value="200",
                    unit="mm",
                ),
            )
        )
        advisory = ValidationIssue(
            rule_id="AI-ADVISORY-001",
            severity=Severity.ERROR,
            message="advisory claims 50 mm",
            category=FindingCategory.IFC_VALIDATION,
            element_guid="guid-known",
            observed_value="50",
            unit="mm",
            origin="advisory",
        )
        merged, _ = gate.reconcile(
            engine_issues=(),
            advisory_issues=(advisory,),
            evidence_universe=universe,
        )
        self.assertEqual(merged[0].severity, Severity.INFO)
        self.assertIn("grounding:reference_resolved", merged[0].evidence_refs)
        self.assertFalse(any("claim_supported" in str(ref) for ref in merged[0].evidence_refs))
        self.assertNotIn("verified_reference", str(merged[0].evidence_refs))


class RT04ResidualLeafTests(unittest.TestCase):
    def test_removed_object_leaf_cannot_remain_in_kept_field(self) -> None:
        guard = PrivacyGuard(tenant_salt="local-deploy-salt")
        with self.assertRaises(PrivacyLeakError):
            guard.mask_payload(
                {
                    "private": {"secret": "CANARY_PRIVATE_739"},
                    "comment": "see CANARY_PRIVATE_739",
                },
                tenant_id="tenant-a",
                rules={"private": "remove", "comment": "keep"},
            )

    def test_benign_keep_still_works(self) -> None:
        guard = PrivacyGuard(tenant_salt="local-deploy-salt")
        result = guard.mask_payload(
            {"comment": "wall thickness 200 mm"},
            tenant_id="tenant-a",
            rules={"comment": "keep"},
        )
        self.assertEqual(result.masked["comment"], "wall thickness 200 mm")


class RT06AgreementBoolTests(unittest.TestCase):
    def test_string_false_is_not_truthy_pass(self) -> None:
        claim = PrecisionClaim(
            metric="macro_precision",
            value=0.91,
            corpus_id="customer-1",
            corpus_kind="customer",
            adjudicators=2,
            date="2026-09-16",
            held_out_split=True,
            fn_tracked=True,
        )
        with self.assertRaises(ValueError):
            precision_claim_publishable_with_agreement(
                claim,
                agreement={"pass_threshold_0_60": "false", "pass_alpha_0_67": True},
            )

    def test_mismatched_corpus_hash_is_not_publishable(self) -> None:
        claim = PrecisionClaim(
            metric="macro_precision",
            value=0.91,
            corpus_id="customer-1",
            corpus_kind="customer",
            adjudicators=2,
            date="2026-09-16",
            held_out_split=True,
            fn_tracked=True,
        )
        ok = precision_claim_publishable_with_agreement(
            claim,
            agreement={
                "pass_threshold_0_60": True,
                "pass_alpha_0_67": True,
                "labels_sha256": "abc",
            },
            expected_corpus_hash="def",
        )
        self.assertFalse(ok)


class RT07EmptySupportTests(unittest.TestCase):
    def test_empty_counts_are_undefined_not_perfect(self) -> None:
        payload = MetricCounts(0, 0, 0).as_dict()
        self.assertIsNone(payload["precision"])
        self.assertIsNone(payload["recall"])
        self.assertTrue(payload["empty_support"])
        self.assertEqual(payload["precision_status"], "undefined_no_predictions")


class RT08DuplicateLabelTests(unittest.TestCase):
    def test_conflicting_duplicates_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dup.csv"
            path.write_text(
                "case_id,finding_id,adjudicator_id,verdict\n"
                "c1,f1,engineer-a,TP\n"
                "c1,f1,engineer-b,TP\n"
                "c1,f1,engineer-a,FP\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "conflicting duplicate"):
                measure_adjudication_csv(path)

    def test_same_finding_id_different_cases_do_not_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["case_id", "finding_id", "adjudicator_id", "verdict"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "case_id": "a",
                        "finding_id": "f1",
                        "adjudicator_id": "engineer-a",
                        "verdict": "TP",
                    }
                )
                writer.writerow(
                    {
                        "case_id": "a",
                        "finding_id": "f1",
                        "adjudicator_id": "engineer-b",
                        "verdict": "TP",
                    }
                )
                writer.writerow(
                    {
                        "case_id": "b",
                        "finding_id": "f1",
                        "adjudicator_id": "engineer-a",
                        "verdict": "FP",
                    }
                )
                writer.writerow(
                    {
                        "case_id": "b",
                        "finding_id": "f1",
                        "adjudicator_id": "engineer-b",
                        "verdict": "FP",
                    }
                )
            payload = measure_adjudication_csv(path)
            self.assertEqual(payload["paired_items"], 2)
            self.assertEqual(payload["items_with_any_label"], 2)
            self.assertIn("source_csv_sha256", payload)

    def test_row_order_does_not_change_kappa(self) -> None:
        rows = [
            "case_id,finding_id,adjudicator_id,verdict",
            "c1,f1,engineer-a,TP",
            "c1,f1,engineer-b,FP",
            "c2,f2,engineer-a,FP",
            "c2,f2,engineer-b,TP",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            left = Path(tmp) / "a.csv"
            right = Path(tmp) / "b.csv"
            left.write_text("\n".join(rows) + "\n", encoding="utf-8")
            right.write_text("\n".join([rows[0], *reversed(rows[1:])]) + "\n", encoding="utf-8")
            a = measure_adjudication_csv(left)
            b = measure_adjudication_csv(right)
            self.assertEqual(a["cohens_kappa"], b["cohens_kappa"])
            self.assertEqual(a["paired_items"], b["paired_items"])


class RT09ParentOpenTests(unittest.TestCase):
    def test_open_storage_file_uses_parent_dirfd_and_windows_handle_path(self) -> None:
        from aerobim.core.security import path_jail as path_jail_module

        source = inspect.getsource(path_jail_module.open_storage_file)
        self.assertIn("_posix_open_at_parent", source)
        self.assertIn("_windows_open_nofollow", source)
        self.assertIn("dir_fd=dirfd", inspect.getsource(path_jail_module._posix_open_at_parent))
        self.assertIn("GetFinalPathNameByHandleW", inspect.getsource(path_jail_module))

    def test_fd_inode_mismatch_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            left = base / "left.bin"
            right = base / "right.bin"
            left.write_bytes(b"L")
            right.write_bytes(b"R")
            with left.open("rb") as handle:
                opened = os.fstat(handle.fileno())
                named = os.lstat(right)
                if (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino):
                    self.skipTest("platform does not distinguish file inodes")
                with self.assertRaises(PathJailError):
                    _assert_fd_still_is_path(handle.fileno(), right)

    def test_windows_case_and_prefix_stay_inside_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            child = base / "nested" / "file.bin"
            child.parent.mkdir()
            child.write_bytes(b"x")
            self.assertTrue(_windows_path_is_under_base(child, base))
            if os.name == "nt":
                self.assertTrue(_windows_path_is_under_base(Path(str(child).swapcase()), base))
            outsider = Path(tmp).resolve().parent / "outside.bin"
            self.assertFalse(_windows_path_is_under_base(outsider, base))

    def test_open_storage_file_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            target = base / "model.ifc"
            with open_storage_file(target, base=base, mode="wb") as handle:
                handle.write(b"ISO-10303-21;")
            with open_storage_file(target, base=base, mode="rb") as handle:
                self.assertEqual(handle.read(), b"ISO-10303-21;")


if __name__ == "__main__":
    unittest.main()
