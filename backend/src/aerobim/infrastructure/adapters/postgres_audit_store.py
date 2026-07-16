from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from aerobim.domain.models import ReportListFilters, ReportSummaryEntry, ValidationReport
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore


def _run_coro(coro):
    """Run an async coroutine from sync code without nesting ``asyncio.run`` unsafely."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


class PostgresAuditStore:
    """Postgres-backed report summary index with filesystem/object payload fallback."""

    def __init__(
        self,
        *,
        db_url: str,
        payload_store: FilesystemAuditStore,
    ) -> None:
        self._payload_store = payload_store
        self._db_url = db_url
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
                discipline
            ) VALUES (
                :report_id,
                :request_id,
                :created_at,
                :passed,
                :issue_count,
                :project_name,
                :discipline
            )
            ON CONFLICT (report_id) DO UPDATE SET
                request_id = EXCLUDED.request_id,
                created_at = EXCLUDED.created_at,
                passed = EXCLUDED.passed,
                issue_count = EXCLUDED.issue_count,
                project_name = EXCLUDED.project_name,
                discipline = EXCLUDED.discipline
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
                discipline
            FROM reports
            WHERE
                (:project IS NULL OR lower(coalesce(project_name, '')) LIKE :project_like)
                AND (:discipline IS NULL OR lower(coalesce(discipline, '')) LIKE :discipline_like)
                AND (:passed IS NULL OR passed = :passed)
            ORDER BY created_at DESC
            """
        )
        _run_coro(self._init_schema())

    def save(self, report: ValidationReport) -> str:
        report_id = self._payload_store.save(report)
        _run_coro(self._index_report(report))
        return report_id

    def get(self, report_id: str) -> ValidationReport | None:
        return self._payload_store.get(report_id)

    def list_reports(
        self,
        filters: ReportListFilters | None = None,
    ) -> list[ReportSummaryEntry]:
        try:
            return _run_coro(self._list_reports_async(filters))
        except Exception:
            # Index unavailable — fall back to payload store filters.
            return self._payload_store.list_reports(filters)

    async def _init_schema(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(self._metadata.create_all)

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
                },
            )

    async def _list_reports_async(
        self,
        filters: ReportListFilters | None,
    ) -> list[ReportSummaryEntry]:
        project = filters.project.strip() if filters and filters.project else None
        discipline = filters.discipline.strip() if filters and filters.discipline else None
        passed = filters.passed if filters else None
        async with self._engine.connect() as conn:
            rows = await conn.execute(
                self._list_sql,
                {
                    "project": project,
                    "project_like": f"%{project.lower()}%" if project else "%",
                    "discipline": discipline,
                    "discipline_like": f"%{discipline.lower()}%" if discipline else "%",
                    "passed": passed,
                },
            )
            entries: list[ReportSummaryEntry] = []
            for row in rows.mappings():
                entries.append(
                    ReportSummaryEntry(
                        report_id=str(row["report_id"]),
                        request_id=str(row["request_id"]),
                        created_at=str(row["created_at"]),
                        passed=bool(row["passed"]),
                        issue_count=int(row["issue_count"]),
                        project_name=row["project_name"],
                        discipline=row["discipline"],
                    )
                )
            return entries
