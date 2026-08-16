from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from aerobim.domain.models import ReportListFilters, ReportSummaryEntry, ValidationReport
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore

REPORTS_TENANT_ID_DDL = "ALTER TABLE reports ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(128)"
MISSING_TENANT_ID_MSG = (
    "reports.tenant_id missing; apply infrastructure/sql/001_reports_tenant_id.sql "
    "as a deploy step, then start with AEROBIM_POSTGRES_APPLY_DDL=0 (RT16-DDL-01)"
)


def _run_coro[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine from sync code without nesting ``asyncio.run`` unsafely."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


class PostgresAuditStore:
    """Postgres-backed report summary index with filesystem/object payload fallback.

    HD5-PGSQL-02 / RT16-DDL-01: default construction runs ``create_all`` plus
    ``ALTER TABLE … ADD COLUMN IF NOT EXISTS tenant_id`` (pilot bootstrap).
    Set ``apply_ddl=False`` (``AEROBIM_POSTGRES_APPLY_DDL=0``) for a DML-only
    role after applying ``infrastructure/sql/001_reports_tenant_id.sql``.
    Missing ``tenant_id`` then raises — never skip the column.
    """

    def __init__(
        self,
        *,
        db_url: str,
        payload_store: FilesystemAuditStore,
        apply_ddl: bool = True,
    ) -> None:
        self._payload_store = payload_store
        self._db_url = db_url
        self._apply_ddl = apply_ddl
        try:
            from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table, text
            from sqlalchemy.ext.asyncio import create_async_engine
        except ModuleNotFoundError as exc:
            raise RuntimeError("PostgresAuditStore requires SQLAlchemy enterprise extras.") from exc

        self._metadata = MetaData()
        self._reports = Table(
            "reports",
            self._metadata,
            Column("report_id", String(32), primary_key=True),
            Column("request_id", String(128), nullable=False),
            Column("created_at", String(64), nullable=False),
            Column("passed", Boolean, nullable=False),
            Column("issue_count", Integer, nullable=False),
            Column("project_name", String(256), nullable=True),
            Column("discipline", String(128), nullable=True),
            Column("tenant_id", String(128), nullable=True),
        )
        self._engine = create_async_engine(db_url)
        self._insert_sql = text(
            """
            INSERT INTO reports (
                report_id,
                request_id,
                created_at,
                passed,
                issue_count,
                project_name,
                discipline,
                tenant_id
            ) VALUES (
                :report_id,
                :request_id,
                :created_at,
                :passed,
                :issue_count,
                :project_name,
                :discipline,
                :tenant_id
            )
            ON CONFLICT (report_id) DO UPDATE SET
                request_id = EXCLUDED.request_id,
                created_at = EXCLUDED.created_at,
                passed = EXCLUDED.passed,
                issue_count = EXCLUDED.issue_count,
                project_name = EXCLUDED.project_name,
                discipline = EXCLUDED.discipline,
                tenant_id = EXCLUDED.tenant_id
            """
        )
        self._list_sql = text(
            """
            SELECT
                report_id,
                request_id,
                created_at,
                passed,
                issue_count,
                project_name,
                discipline,
                tenant_id
            FROM reports
            WHERE
                (:project IS NULL OR lower(coalesce(project_name, '')) LIKE :project_like)
                AND (:discipline IS NULL OR lower(coalesce(discipline, '')) LIKE :discipline_like)
                AND (:passed IS NULL OR passed = :passed)
                AND (:tenant_id IS NULL OR tenant_id = :tenant_id)
            ORDER BY created_at DESC
            """
        )
        self._peek_tenant_sql = text("SELECT tenant_id FROM reports WHERE report_id = :report_id")
        self._alter_tenant_sql = text(REPORTS_TENANT_ID_DDL)
        self._tenant_probe_sql = text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = current_schema() "
            "AND table_name = 'reports' AND column_name = 'tenant_id'"
        )
        _run_coro(self._init_schema())

    def save(self, report: ValidationReport) -> str:
        report_id = self._payload_store.save(report)
        _run_coro(self._index_report(report))
        return report_id

    def get(self, report_id: str) -> ValidationReport | None:
        return self._payload_store.get(report_id)

    def peek_tenant_id(self, report_id: str) -> str | None:
        try:
            peeked = _run_coro(self._peek_tenant_id_async(report_id))
        except Exception:
            peeked = None
        if peeked:
            return peeked
        return self._payload_store.peek_tenant_id(report_id)

    def list_reports(
        self,
        filters: ReportListFilters | None = None,
    ) -> list[ReportSummaryEntry]:
        try:
            return _run_coro(self._list_reports_async(filters))
        except Exception:
            if getattr(self._payload_store, "_fail_closed", False):
                raise
            return self._payload_store.list_reports(filters)

    async def _init_schema(self) -> None:
        async with self._engine.begin() as conn:
            if self._apply_ddl:
                await conn.run_sync(self._metadata.create_all)
                await conn.execute(self._alter_tenant_sql)
                return
            row = await conn.execute(self._tenant_probe_sql)
            if row.first() is None:
                raise RuntimeError(MISSING_TENANT_ID_MSG)

    async def _index_report(self, report: ValidationReport) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(
                self._insert_sql,
                {
                    "report_id": report.report_id,
                    "request_id": report.request_id,
                    "created_at": report.created_at,
                    "passed": report.summary.passed,
                    "issue_count": report.summary.issue_count,
                    "project_name": report.project_name,
                    "discipline": report.discipline,
                    "tenant_id": (report.tenant_id or "").strip() or None,
                },
            )

    async def _list_reports_async(
        self,
        filters: ReportListFilters | None,
    ) -> list[ReportSummaryEntry]:
        project = filters.project.strip() if filters and filters.project else None
        discipline = filters.discipline.strip() if filters and filters.discipline else None
        passed = filters.passed if filters else None
        tenant_id = (
            filters.tenant_id.strip() if filters and (filters.tenant_id or "").strip() else None
        )
        async with self._engine.connect() as conn:
            rows = await conn.execute(
                self._list_sql,
                {
                    "project": project,
                    "project_like": f"%{project.lower()}%" if project else "%",
                    "discipline": discipline,
                    "discipline_like": f"%{discipline.lower()}%" if discipline else "%",
                    "passed": passed,
                    "tenant_id": tenant_id,
                },
            )
            entries: list[ReportSummaryEntry] = []
            for row in rows.mappings():
                tenant_value = row.get("tenant_id")
                entries.append(
                    ReportSummaryEntry(
                        report_id=str(row["report_id"]),
                        request_id=str(row["request_id"]),
                        created_at=str(row["created_at"]),
                        passed=bool(row["passed"]),
                        issue_count=int(row["issue_count"]),
                        project_name=row["project_name"],
                        discipline=row["discipline"],
                        tenant_id=str(tenant_value) if tenant_value else None,
                    )
                )
            return entries

    async def _peek_tenant_id_async(self, report_id: str) -> str | None:
        async with self._engine.connect() as conn:
            row = await conn.execute(self._peek_tenant_sql, {"report_id": report_id})
            mapping = row.mappings().first()
            if mapping is None:
                return None
            tenant = mapping.get("tenant_id")
            if isinstance(tenant, str) and tenant.strip():
                return tenant.strip()
            return None
