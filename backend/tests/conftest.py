"""Shared pytest setup for the backend suite.

AER-03 / SOTA-A3: ifctester builds its IDS XMLSchema lazily on the first
``ids.open`` and caches it in ``ifctester.ids.schema``. Without a URI mapper,
building it imports W3C XSDs over HTTP from ``www.w3.org``. Pre-installing the
offline schema (mapped to ``xmlschema``'s bundled W3C schemas with
``allow='local'``) guarantees zero network egress and instant startup.
"""

from __future__ import annotations

import pytest


def _prewarm_ifctester_schema() -> None:
    from aerobim.infrastructure.adapters.xml_ids_document_auditor import (
        ensure_ifctester_offline_schema,
    )

    ensure_ifctester_offline_schema()


def pytest_sessionstart(session: pytest.Session) -> None:
    if session.config.option.collectonly:
        return
    _prewarm_ifctester_schema()
