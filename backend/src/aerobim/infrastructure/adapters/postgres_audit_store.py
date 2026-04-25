from __future__ import annotations

import asyncio

from aerobim.domain.models import ReportSummaryEntry, ValidationReport
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore


class PostgresAuditStore:
    """Postgres-backed report summary index with filesystem/object payload fallback.

    This foundation pass keeps full report payload round-tripping in the existing
    JSON/object store path while indexing report summaries in Postgres when the
    optional enterprise dependencies are installed.
    """

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
        asyncio.run(self._init_schema())

    def save(self, report: ValidationReport) -> str:
        report_id = self._payload_store.save(report)
        asyncio.run(self._index_report(report))
        return report_id

    def get(self, report_id: str) -> ValidationReport | None:
        return self._payload_store.get(report_id)

    def list_reports(self) -> list[ReportSummaryEntry]:
        return self._payload_store.list_reports()

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
