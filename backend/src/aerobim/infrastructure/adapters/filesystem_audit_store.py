from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from aerobim.core.security.path_jail import open_storage_file
from aerobim.domain.finding_provenance import assert_finding_persistable, ensure_finding_provenance
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    ClashResult,
    ComparisonOperator,
    ConflictKind,
    DivergenceRecord,
    DrawingAnnotation,
    DrawingAsset,
    DrawingRegionRef,
    FindingCategory,
    GeneratedRemark,
    ParsedRequirement,
    ProblemZone,
    ReportCapabilities,
    ReportListFilters,
    ReportSummaryEntry,
    RuleScope,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.norm_assist import IdsCompileDraft
from aerobim.domain.persistence import (
    ReportCommitState,
    build_commit_manifest_payload,
    is_report_reviewable,
)
from aerobim.domain.ports import ObjectStore
from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore

_LOCK_ATTEMPTS = 50
_LOCK_SLEEP_S = 0.02
_PDF_OPEN_TIMEOUT_S = 30.0
_logger = logging.getLogger(__name__)


class ReportIntegrityError(RuntimeError):
    """Raised when report JSON does not match the commit manifest digest."""


class FilesystemAuditStore:
    """Persists validation reports as JSON files with atomic writes."""

    def __init__(
        self,
        storage_dir: Path,
        *,
        object_store: ObjectStore | None = None,
        report_ttl_days: int | None = None,
        fail_closed: bool = False,
    ) -> None:
        self._storage_dir = storage_dir.resolve()
        self._reports_dir = self._storage_dir / "reports"
        self._drawing_assets_dir = self._storage_dir / "drawing-assets"
        self._object_store = object_store or LocalObjectStore(self._storage_dir)
        self._report_ttl_days = report_ttl_days if report_ttl_days and report_ttl_days > 0 else None
        self._fail_closed = fail_closed
        self._reports_dir.mkdir(parents=True, exist_ok=True)
        self._drawing_assets_dir.mkdir(parents=True, exist_ok=True)

    def save(self, report: ValidationReport) -> str:
        self._prune_expired_reports()
        stamped_issues = tuple(ensure_finding_provenance(issue) for issue in report.issues)
        for issue in stamped_issues:
            assert_finding_persistable(issue)
        report = ValidationReport(
            **{**report.__dict__, "issues": stamped_issues},
        )
        artifact_keys: list[str] = []
        lock_path = self._reports_dir / f"{report.report_id}.save.lock"
        self._acquire_exclusive_lock(lock_path)
        try:
            persisted_report = self._materialize_report(report, artifact_keys=artifact_keys)
            data = self._serialize_report(persisted_report)
            payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            report_sha256 = hashlib.sha256(payload).hexdigest()
            target = self._reports_dir / f"{report.report_id}.json"
            tmp = self._reports_dir / f"{report.report_id}.tmp"
            tmp.write_bytes(payload)
            os.replace(str(tmp), str(target))
            self._write_commit_manifest(
                report.report_id,
                artifact_keys=artifact_keys,
                ifc_object_key=persisted_report.ifc_object_key,
                report_sha256=report_sha256,
                report_byte_length=len(payload),
            )
            return report.report_id
        except Exception:
            self._record_orphan(report.report_id, artifact_keys=artifact_keys)
            raise
        finally:
            lock_path.unlink(missing_ok=True)

    def _acquire_exclusive_lock(self, lock_path: Path) -> None:
        for _ in range(_LOCK_ATTEMPTS):
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                try:
                    os.write(fd, b"1")
                finally:
                    os.close(fd)
                return
            except FileExistsError:
                time.sleep(_LOCK_SLEEP_S)
        raise RuntimeError(f"Could not acquire report-save lock for {lock_path.name}")

    def is_report_committed(self, report_id: str) -> bool:
        return self._commit_marker_path(report_id).exists()

    def is_report_reviewable(self, report_id: str) -> bool:
        return is_report_reviewable(
            committed=self.is_report_committed(report_id),
            report_json_exists=self._report_json_path(report_id).exists(),
        )

    def list_orphan_report_ids(self) -> list[str]:
        orphan_dir = self._storage_dir / "orphans"
        if not orphan_dir.exists():
            return []
        return sorted(path.stem for path in orphan_dir.glob("*.json"))

    def _report_json_path(self, report_id: str) -> Path:
        return self._reports_dir / f"{report_id}.json"

    def _commit_marker_path(self, report_id: str) -> Path:
        return self._reports_dir / f"{report_id}.committed.json"

    def _iter_report_json_paths(self):
        for path in sorted(self._reports_dir.glob("*.json")):
            name = path.name
            if name.endswith(".committed.json") or name.endswith(".tmp"):
                continue
            if ".committed." in name:
                continue
            yield path

    def _write_commit_manifest(
        self,
        report_id: str,
        *,
        artifact_keys: list[str],
        ifc_object_key: str | None,
        report_sha256: str | None = None,
        report_byte_length: int | None = None,
    ) -> None:
        manifest = build_commit_manifest_payload(
            report_id=report_id,
            artifact_keys=artifact_keys,
            ifc_object_key=ifc_object_key,
            committed_at=datetime.now(tz=UTC).isoformat(),
            commit_state=ReportCommitState.REVIEWABLE,
            report_sha256=report_sha256,
            report_byte_length=report_byte_length,
        )
        target = self._commit_marker_path(report_id)
        tmp = self._reports_dir / f"{report_id}.committed.tmp"
        tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(str(tmp), str(target))

    def _record_orphan(self, report_id: str, *, artifact_keys: list[str]) -> None:
        orphan_dir = self._storage_dir / "orphans"
        orphan_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0.0",
            "report_id": report_id,
            "artifact_keys": list(artifact_keys),
            "consistency_state": ReportCommitState.ORPHAN_UNCOMMITTED.value,
            "recorded_at": datetime.now(tz=UTC).isoformat(),
        }
        (orphan_dir / f"{report_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _materialize_report(
        self,
        report: ValidationReport,
        *,
        artifact_keys: list[str] | None = None,
    ) -> ValidationReport:
        keys = artifact_keys if artifact_keys is not None else []
        ifc_object_key = report.ifc_object_key or self._materialize_ifc_source(
            report.report_id,
            report.ifc_path,
            artifact_keys=keys,
            tenant_id=report.tenant_id,
        )
        drawing_assets = tuple(
            self._materialize_drawing_assets(
                report.report_id,
                report.drawing_assets,
                artifact_keys=keys,
                tenant_id=report.tenant_id,
            )
        )
        return ValidationReport(
            report_id=report.report_id,
            request_id=report.request_id,
            ifc_path=report.ifc_path,
            ifc_object_key=ifc_object_key,
            created_at=report.created_at,
            requirements=report.requirements,
            issues=report.issues,
            summary=report.summary,
            drawing_annotations=report.drawing_annotations,
            drawing_assets=drawing_assets,
            clash_results=report.clash_results,
            capabilities=report.capabilities,
            schema_validation_request_id=report.schema_validation_request_id,
            project_name=report.project_name,
            discipline=report.discipline,
            stage=report.stage,
            information_container_id=report.information_container_id,
            revision=report.revision,
            doc_status=report.doc_status,
            tenant_id=report.tenant_id,
            project_id=report.project_id,
            divergences=report.divergences,
            advisory_ids_draft=report.advisory_ids_draft,
            drawing_regions=report.drawing_regions,
            annotation_ifc_links=report.annotation_ifc_links,
            tool_traces=report.tool_traces,
            schema_version=report.schema_version,
        )

    def _serialize_report(self, report: ValidationReport) -> dict[str, object]:
        data = asdict(report)
        data["ifc_path"] = str(report.ifc_path)
        data["ifc_object_key"] = report.ifc_object_key
        data["drawing_assets"] = [
            {
                "asset_id": asset.asset_id,
                "sheet_id": asset.sheet_id,
                "page_number": asset.page_number,
                "media_type": asset.media_type,
                "coordinate_width": asset.coordinate_width,
                "coordinate_height": asset.coordinate_height,
                "stored_filename": asset.stored_filename,
                "object_key": asset.object_key,
            }
            for asset in report.drawing_assets
        ]
        return data

    def _tenant_prefixed_key(
        self,
        *,
        kind: str,
        report_id: str,
        name: str,
        tenant_id: str | None,
    ) -> str:
        relative = f"{kind}/{report_id}/{name}"
        tenant = (tenant_id or "").strip()
        if not tenant:
            return relative
        from aerobim.core.security.path_jail import safe_storage_token

        safe = safe_storage_token(tenant)
        return f"tenants/{safe}/{relative}"

    def _materialize_ifc_source(
        self,
        report_id: str,
        ifc_path: Path,
        *,
        artifact_keys: list[str] | None = None,
        tenant_id: str | None = None,
    ) -> str | None:
        if not ifc_path.exists() or not ifc_path.is_file():
            return None
        object_key = self._tenant_prefixed_key(
            kind="ifc-sources",
            report_id=report_id,
            name=ifc_path.name,
            tenant_id=tenant_id,
        )
        self._object_store.put_bytes(
            object_key,
            ifc_path.read_bytes(),
            content_type="application/octet-stream",
        )
        if artifact_keys is not None:
            artifact_keys.append(object_key)
        return object_key

    def _materialize_drawing_assets(
        self,
        report_id: str,
        drawing_assets: tuple[DrawingAsset, ...],
        *,
        artifact_keys: list[str] | None = None,
        tenant_id: str | None = None,
    ) -> list[DrawingAsset]:
        if not drawing_assets:
            return []

        report_asset_dir = self._drawing_assets_dir / report_id
        if report_asset_dir.exists():
            shutil.rmtree(report_asset_dir)
        report_asset_dir.mkdir(parents=True, exist_ok=True)

        persisted_assets: list[DrawingAsset] = []
        for asset in drawing_assets:
            if asset.source_path is None:
                persisted_assets.append(asset)
                continue
            persisted = self._persist_document_asset(
                report_id,
                asset,
                tenant_id=tenant_id,
            )
            persisted_assets.extend(persisted)
            if artifact_keys is not None:
                for item in persisted:
                    if item.object_key:
                        artifact_keys.append(item.object_key)
        return persisted_assets

    def _persist_document_asset(
        self,
        report_id: str,
        asset: DrawingAsset,
        *,
        tenant_id: str | None = None,
    ) -> list[DrawingAsset]:
        try:
            import pymupdf
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Drawing asset preview generation requires PyMuPDF. Install the 'raster' extra."
            ) from exc

        source_path = asset.source_path
        if source_path is None:
            return [asset]
        if not source_path.exists():
            raise FileNotFoundError(source_path)

        if source_path.suffix.lower() != ".pdf":
            return [
                self._persist_raster_asset(
                    report_id,
                    asset,
                    source_path,
                    pymupdf,
                    tenant_id=tenant_id,
                )
            ]

        persisted_assets: list[DrawingAsset] = []

        def _render_pdf_pages() -> list[DrawingAsset]:
            pages: list[DrawingAsset] = []
            with pymupdf.open(source_path) as document:
                for page_index, page in enumerate(document, start=1):
                    if asset.page_number is not None and page_index != asset.page_number:
                        continue
                    pix = page.get_pixmap(dpi=144, annots=False)
                    persisted_asset_id = asset.asset_id
                    if document.page_count > 1 or asset.page_number is None:
                        persisted_asset_id = f"{asset.asset_id}-page-{page_index:03d}"
                    stored_filename = f"{persisted_asset_id}.png"
                    object_key = self._store_preview_bytes(
                        report_id,
                        stored_filename,
                        pix.tobytes("png"),
                        tenant_id=tenant_id,
                    )
                    pages.append(
                        DrawingAsset(
                            asset_id=persisted_asset_id,
                            sheet_id=asset.sheet_id,
                            page_number=page_index,
                            media_type="image/png",
                            coordinate_width=float(page.rect.width),
                            coordinate_height=float(page.rect.height),
                            stored_filename=stored_filename,
                            object_key=object_key,
                        )
                    )
            return pages

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_render_pdf_pages)
            try:
                persisted_assets = future.result(timeout=_PDF_OPEN_TIMEOUT_S)
            except FuturesTimeout as exc:
                raise TimeoutError(
                    f"PDF preview timed out after {_PDF_OPEN_TIMEOUT_S:.0f}s: {source_path}"
                ) from exc
        return persisted_assets

    def _persist_raster_asset(
        self,
        report_id: str,
        asset: DrawingAsset,
        source_path: Path,
        pymupdf_module,
        *,
        tenant_id: str | None = None,
    ) -> DrawingAsset:
        suffix = source_path.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            media_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
            }[suffix]
            stored_filename = f"{asset.asset_id}{suffix}"
            payload = source_path.read_bytes()
            object_key = self._store_preview_bytes(
                report_id,
                stored_filename,
                payload,
                content_type=media_type,
                tenant_id=tenant_id,
            )
            width = asset.coordinate_width
            height = asset.coordinate_height
            if width is None or height is None:
                try:
                    pix = pymupdf_module.Pixmap(str(source_path))
                    width = float(pix.width)
                    height = float(pix.height)
                except Exception:  # noqa: BLE001
                    width = width
                    height = height
            return DrawingAsset(
                asset_id=asset.asset_id,
                sheet_id=asset.sheet_id,
                page_number=asset.page_number or 1,
                media_type=media_type,
                coordinate_width=width,
                coordinate_height=height,
                stored_filename=stored_filename,
                object_key=object_key,
            )

        pix = pymupdf_module.Pixmap(str(source_path))
        stored_filename = f"{asset.asset_id}.png"
        object_key = self._store_preview_bytes(
            report_id,
            stored_filename,
            pix.tobytes("png"),
            tenant_id=tenant_id,
        )
        return DrawingAsset(
            asset_id=asset.asset_id,
            sheet_id=asset.sheet_id,
            page_number=asset.page_number or 1,
            media_type="image/png",
            coordinate_width=float(pix.width),
            coordinate_height=float(pix.height),
            stored_filename=stored_filename,
            object_key=object_key,
        )

    def _store_preview_bytes(
        self,
        report_id: str,
        stored_filename: str,
        payload: bytes,
        *,
        content_type: str = "image/png",
        tenant_id: str | None = None,
    ) -> str:
        object_key = self._tenant_prefixed_key(
            kind="drawing-assets",
            report_id=report_id,
            name=stored_filename,
            tenant_id=tenant_id,
        )
        self._object_store.put_bytes(object_key, payload, content_type=content_type)
        return object_key

    def get(self, report_id: str) -> ValidationReport | None:
        self._prune_expired_reports()
        target = self._report_json_path(report_id)
        if not target.exists():
            return None
        # Uncommitted JSON is not reviewable — hide from consumers.
        if not self.is_report_committed(report_id):
            return None
        try:
            with open_storage_file(target, base=self._storage_dir, mode="rb") as handle:
                raw = handle.read()
            if not self._verify_report_integrity(report_id, raw):
                return None
            data = json.loads(raw.decode("utf-8"))
            report = self._reconstruct_report(data)
            if self._is_expired(report):
                self._delete_report_files(report, target)
                return None
            return report
        except ReportIntegrityError:
            if self._fail_closed:
                raise
            return None
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, UnicodeDecodeError):
            return None

    def discard(self, report_id: str) -> bool:
        """Remove report JSON, commit marker, and drawing assets (cancel tombstone)."""

        report_id = (report_id or "").strip()
        if not report_id:
            return False
        target = self._report_json_path(report_id)
        report: ValidationReport | None = None
        if target.exists():
            try:
                data = json.loads(target.read_text(encoding="utf-8"))
                report = self._reconstruct_report(data)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
                report = None
        if report is not None:
            self._delete_report_files(report, target)
            return True
        # Best-effort cleanup when JSON is missing/corrupt.
        commit_path = self._commit_marker_path(report_id)
        assets_dir = self._drawing_assets_dir / report_id
        removed = False
        if assets_dir.exists():
            shutil.rmtree(assets_dir, ignore_errors=True)
            removed = True
        if commit_path.exists():
            commit_path.unlink(missing_ok=True)
            removed = True
        if target.exists():
            target.unlink(missing_ok=True)
            removed = True
        return removed

    def _verify_report_integrity(self, report_id: str, raw: bytes) -> bool:
        commit_path = self._commit_marker_path(report_id)
        if not commit_path.exists():
            return False
        try:
            commit = json.loads(commit_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            if self._fail_closed:
                raise ReportIntegrityError(
                    f"Report {report_id} commit manifest unreadable"
                ) from exc
            _logger.warning("Report %s commit manifest unreadable; denying", report_id)
            return False
        expected = commit.get("report_sha256")
        if not expected:
            # Legacy commits without digest remain readable.
            return True
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            message = f"Report {report_id} integrity mismatch (sha256)"
            if self._fail_closed:
                raise ReportIntegrityError(message)
            _logger.warning("%s; denying", message)
            return False
        return True

    def list_reports(
        self,
        filters: ReportListFilters | None = None,
    ) -> list[ReportSummaryEntry]:
        self._prune_expired_reports()
        entries: list[ReportSummaryEntry] = []
        for path in self._iter_report_json_paths():
            report_id = path.stem
            if not self.is_report_committed(report_id):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                report = self._reconstruct_report(data)
                if self._is_expired(report):
                    self._delete_report_files(report, path)
                    continue
                summary = data.get("summary", {})
                entries.append(
                    ReportSummaryEntry(
                        report_id=data["report_id"],
                        request_id=data["request_id"],
                        created_at=data["created_at"],
                        passed=summary.get("passed", False),
                        issue_count=summary.get("issue_count", 0),
                        project_name=data.get("project_name"),
                        discipline=data.get("discipline"),
                        tenant_id=data.get("tenant_id"),
                    )
                )
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
        from aerobim.application.services.report_list_filters import apply_report_list_filters

        return apply_report_list_filters(entries, filters)

    def _reconstruct_report(self, data: dict) -> ValidationReport:
        return ValidationReport(
            report_id=data["report_id"],
            request_id=data["request_id"],
            ifc_path=Path(data["ifc_path"]),
            ifc_object_key=data.get("ifc_object_key"),
            created_at=data["created_at"],
            requirements=tuple(
                self._reconstruct_requirement(r) for r in data.get("requirements", [])
            ),
            issues=tuple(self._reconstruct_issue(i) for i in data.get("issues", [])),
            summary=self._reconstruct_summary(data.get("summary", {})),
            drawing_annotations=tuple(
                self._reconstruct_annotation(a) for a in data.get("drawing_annotations", [])
            ),
            drawing_assets=tuple(
                self._reconstruct_drawing_asset(a) for a in data.get("drawing_assets", [])
            ),
            clash_results=tuple(
                self._reconstruct_clash_result(c) for c in data.get("clash_results", [])
            ),
            capabilities=self._reconstruct_capabilities(data.get("capabilities")),
            schema_validation_request_id=data.get("schema_validation_request_id"),
            project_name=data.get("project_name"),
            discipline=data.get("discipline"),
            stage=data.get("stage"),
            information_container_id=data.get("information_container_id"),
            revision=data.get("revision"),
            doc_status=data.get("doc_status"),
            tenant_id=data.get("tenant_id"),
            project_id=data.get("project_id"),
            divergences=tuple(
                self._reconstruct_divergence(item) for item in data.get("divergences", [])
            ),
            advisory_ids_draft=self._reconstruct_ids_draft(data.get("advisory_ids_draft")),
            drawing_regions=tuple(
                self._reconstruct_drawing_region(item) for item in data.get("drawing_regions", [])
            ),
            annotation_ifc_links=tuple(
                item
                for item in data.get("annotation_ifc_links", [])
                if isinstance(item, dict)
            ),
            tool_traces=tuple(
                item for item in data.get("tool_traces", []) if isinstance(item, dict)
            ),
            schema_version=str(data.get("schema_version") or "1.0.0"),
        )

    def _reconstruct_requirement(self, data: dict) -> ParsedRequirement:
        return ParsedRequirement(
            rule_id=data["rule_id"],
            ifc_entity=data.get("ifc_entity"),
            rule_scope=RuleScope(data["rule_scope"])
            if data.get("rule_scope")
            else RuleScope.IFC_PROPERTY,
            target_ref=data.get("target_ref"),
            property_set=data.get("property_set"),
            property_name=data.get("property_name"),
            operator=ComparisonOperator(data["operator"])
            if data.get("operator")
            else ComparisonOperator.EQUALS,
            expected_value=data.get("expected_value"),
            unit=data.get("unit"),
            source=data.get("source", ""),
            source_kind=SourceKind(data["source_kind"])
            if data.get("source_kind")
            else SourceKind.STRUCTURED_TEXT,
            evidence_text=data.get("evidence_text"),
            instructions=data.get("instructions"),
            evidence_modality=data.get("evidence_modality"),
            confidence=data.get("confidence"),
            norm_source=data.get("norm_source"),
            norm_edition=data.get("norm_edition"),
            norm_clause=data.get("norm_clause"),
            approval_status=data.get("approval_status"),
            approval_ref=data.get("approval_ref"),
        )

    def _reconstruct_issue(self, data: dict) -> ValidationIssue:
        problem_zone_data = data.get("problem_zone")
        remark_data = data.get("remark")
        return ValidationIssue(
            rule_id=data["rule_id"],
            severity=Severity(data["severity"]),
            message=data["message"],
            ifc_entity=data.get("ifc_entity"),
            category=FindingCategory(data["category"])
            if data.get("category")
            else FindingCategory.IFC_VALIDATION,
            target_ref=data.get("target_ref"),
            property_set=data.get("property_set"),
            property_name=data.get("property_name"),
            operator=ComparisonOperator(data["operator"]) if data.get("operator") else None,
            expected_value=data.get("expected_value"),
            observed_value=data.get("observed_value"),
            unit=data.get("unit"),
            element_guid=data.get("element_guid"),
            problem_zone=ProblemZone(**problem_zone_data) if problem_zone_data else None,
            remark=GeneratedRemark(**remark_data) if remark_data else None,
            conflict_kind=ConflictKind(data["conflict_kind"])
            if data.get("conflict_kind")
            else None,
            priority=data.get("priority", 0),
            source_id=data.get("source_id"),
            evidence_modality=data.get("evidence_modality"),
            confidence=data.get("confidence"),
            norm_source=data.get("norm_source"),
            norm_edition=data.get("norm_edition"),
            norm_clause=data.get("norm_clause"),
            approval_status=data.get("approval_status"),
            approval_ref=data.get("approval_ref"),
            rase_elements=tuple(data.get("rase_elements") or ()),
            finding_id=data.get("finding_id"),
            evidence_refs=tuple(data.get("evidence_refs") or ()),
            tenant_id=data.get("tenant_id"),
            project_id=data.get("project_id"),
            origin=data.get("origin"),
        )

    def _reconstruct_summary(self, data: dict) -> ValidationSummary:
        from aerobim.domain.package_outcome import PackageOutcome

        raw_outcome = data.get("outcome")
        outcome: PackageOutcome | None = None
        if raw_outcome is not None:
            try:
                outcome = PackageOutcome(str(raw_outcome))
            except ValueError:
                outcome = None
        return ValidationSummary(
            requirement_count=data.get("requirement_count", 0),
            issue_count=data.get("issue_count", 0),
            error_count=data.get("error_count", 0),
            warning_count=data.get("warning_count", 0),
            passed=data.get("passed", False),
            drawing_annotation_count=data.get("drawing_annotation_count", 0),
            generated_remark_count=data.get("generated_remark_count", 0),
            authoritative=bool(data.get("authoritative", False)),
            outcome=outcome,
        )

    def _reconstruct_capability_status(
        self,
        data: object,
        *,
        default: CapabilityStatus | None = None,
    ) -> CapabilityStatus:
        if not isinstance(data, dict):
            return default or CapabilityStatus(CapabilityState.SKIPPED, "missing capability status")
        raw_status = str(data.get("status", "skipped"))
        try:
            status = CapabilityState(raw_status)
        except ValueError:
            status = CapabilityState.SKIPPED
        reason = data.get("reason")
        external_ref = data.get("external_ref")
        return CapabilityStatus(
            status=status,
            reason=str(reason) if reason is not None else None,
            external_ref=str(external_ref) if external_ref is not None else None,
        )

    def _reconstruct_capabilities(self, data: object) -> ReportCapabilities | None:
        if not isinstance(data, dict):
            return None
        return ReportCapabilities(
            clash=self._reconstruct_capability_status(data.get("clash")),
            ids=self._reconstruct_capability_status(data.get("ids")),
            ifc_validation=self._reconstruct_capability_status(data.get("ifc_validation")),
            unit_scale=self._reconstruct_capability_status(data.get("unit_scale")),
            raster=self._reconstruct_capability_status(data.get("raster")),
            ifc_schema=self._reconstruct_capability_status(data.get("ifc_schema")),
            norm_rule_packs=self._reconstruct_capability_status(data.get("norm_rule_packs")),
            section_pairing=self._reconstruct_capability_status(data.get("section_pairing")),
            dwg_dxf=self._reconstruct_capability_status(
                data.get("dwg_dxf"),
                default=CapabilityStatus(
                    CapabilityState.MISSING, "DWG/DXF native analysis not implemented"
                ),
            ),
            cv_human_level=self._reconstruct_capability_status(
                data.get("cv_human_level"),
                default=CapabilityStatus(
                    CapabilityState.MISSING,
                    "Human-level CV/drawing understanding not implemented",
                ),
            ),
            mep_system_clash=self._reconstruct_capability_status(
                data.get("mep_system_clash"),
                default=CapabilityStatus(
                    CapabilityState.NOT_VERIFIED,
                    "MEP system graph provider DI-wired but unconfigured (MEP-CLASH-001); "
                    "system-aware clash NOT VERIFIED",
                ),
            ),
            calculation_match=self._reconstruct_capability_status(
                data.get("calculation_match"),
                default=CapabilityStatus(
                    CapabilityState.SKIPPED, "numeric calculation match not evaluated"
                ),
            ),
            calculation_correctness=self._reconstruct_capability_status(
                data.get("calculation_correctness"),
                default=CapabilityStatus(
                    CapabilityState.NOT_IMPLEMENTED,
                    "Independent calculation correctness verification not implemented",
                ),
            ),
            quantity=self._reconstruct_capability_status(
                data.get("quantity"),
                default=CapabilityStatus(
                    CapabilityState.SKIPPED, "quantity consistency not evaluated"
                ),
            ),
        )

    def _reconstruct_annotation(self, data: dict) -> DrawingAnnotation:
        problem_zone_data = data.get("problem_zone")
        return DrawingAnnotation(
            annotation_id=data["annotation_id"],
            sheet_id=data["sheet_id"],
            target_ref=data["target_ref"],
            measure_name=data["measure_name"],
            observed_value=data["observed_value"],
            unit=data.get("unit"),
            problem_zone=ProblemZone(**problem_zone_data) if problem_zone_data else None,
            source=data.get("source", "drawing-text"),
        )

    def _reconstruct_divergence(self, data: dict) -> DivergenceRecord:
        return DivergenceRecord(
            finding_key=data["finding_key"],
            engine_verdict=data["engine_verdict"],
            advisory_verdict=data["advisory_verdict"],
            resolution=data.get("resolution", "engine_wins"),
        )

    def _reconstruct_ids_draft(self, data: dict | None) -> IdsCompileDraft | None:
        if not data:
            return None
        return IdsCompileDraft(
            suggested_ids_xml=data.get("suggested_ids_xml", ""),
            rationale=data.get("rationale", ""),
            source_requirement_count=int(data.get("source_requirement_count", 0)),
            advisory_only=bool(data.get("advisory_only", True)),
            confidence=float(data.get("confidence", 0.4)),
            rase_elements=tuple(data.get("rase_elements") or ()),
            rase_summary=data.get("rase_summary"),
        )

    def _reconstruct_drawing_region(self, data: dict) -> DrawingRegionRef:
        bbox = data.get("bbox_xyxy") or (0.0, 0.0, 0.0, 0.0)
        return DrawingRegionRef(
            sheet_id=data["sheet_id"],
            bbox_xyxy=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
            confidence=float(data.get("confidence", 0.0)),
            modality=str(data.get("modality", "ocr")),
            hitl_required=bool(data.get("hitl_required", False)),
            hitl_reason=data.get("hitl_reason"),
        )

    def _reconstruct_drawing_asset(self, data: dict) -> DrawingAsset:
        return DrawingAsset(
            asset_id=data["asset_id"],
            sheet_id=data["sheet_id"],
            page_number=data.get("page_number"),
            media_type=data.get("media_type", "image/png"),
            coordinate_width=data.get("coordinate_width"),
            coordinate_height=data.get("coordinate_height"),
            stored_filename=data.get("stored_filename"),
            object_key=data.get("object_key"),
            source_path=Path(data["source_path"]) if data.get("source_path") else None,
        )

    def _reconstruct_clash_result(self, data: dict) -> ClashResult:
        return ClashResult(
            element_a_guid=data["element_a_guid"],
            element_b_guid=data["element_b_guid"],
            clash_type=data["clash_type"],
            distance=data["distance"],
            description=data["description"],
        )

    def _prune_expired_reports(self) -> None:
        if self._report_ttl_days is None:
            return
        for path in self._iter_report_json_paths():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                report = self._reconstruct_report(data)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            if self._is_expired(report):
                self._delete_report_files(report, path)

    def _is_expired(self, report: ValidationReport) -> bool:
        if self._report_ttl_days is None:
            return False
        created_at = self._parse_created_at(report.created_at)
        if created_at is None:
            return False
        return datetime.now(tz=UTC) - created_at > timedelta(days=self._report_ttl_days)

    def _parse_created_at(self, value: str) -> datetime | None:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    def _delete_report_files(self, report: ValidationReport, report_path: Path) -> None:
        report_id = report.report_id
        # Prefer keys from commit manifest when present (complete artifact set).
        commit_path = self._commit_marker_path(report_id)
        artifact_keys: list[str] = []
        if commit_path.exists():
            try:
                commit_data = json.loads(commit_path.read_text(encoding="utf-8"))
                artifact_keys = [str(k) for k in (commit_data.get("artifact_keys") or [])]
            except (json.JSONDecodeError, OSError):
                artifact_keys = []
        if report.ifc_object_key:
            artifact_keys.append(report.ifc_object_key)
        for asset in report.drawing_assets:
            if asset.object_key:
                artifact_keys.append(asset.object_key)
        seen: set[str] = set()
        for key in artifact_keys:
            if key in seen:
                continue
            seen.add(key)
            try:
                self._object_store.delete(key)
            except Exception:  # noqa: BLE001 — best-effort TTL cleanup
                pass
        assets_dir = self._drawing_assets_dir / report_id
        if assets_dir.exists():
            shutil.rmtree(assets_dir, ignore_errors=True)
        review_events = self._storage_dir / "review-events" / f"{report_id}.jsonl"
        if review_events.exists():
            review_events.unlink(missing_ok=True)
        orphan_record = self._storage_dir / "orphans" / f"{report_id}.json"
        if orphan_record.exists():
            orphan_record.unlink(missing_ok=True)
        if commit_path.exists():
            commit_path.unlink(missing_ok=True)
        if report_path.exists():
            report_path.unlink(missing_ok=True)
