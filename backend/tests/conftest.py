"""Shared pytest setup for the backend suite.

AER-03: ifctester builds its IDS XMLSchema lazily on the first ``ids.open`` and
caches it in ``ifctester.ids.schema``. Building it imports W3C XSDs over the
network with xmlschema's default 300 s timeout. On a host where outbound
traffic is silently dropped, that first call can sit in ``connect()`` inside a
TestClient worker thread, where pytest-timeout cannot interrupt it, and the run
hangs. Building the same schema once here, in the main thread and with a short
fetch timeout, keeps a full local run finite. With network access the result is
the same schema ifctester would build itself. The permanent fix (local W3C XSDs
via a URI mapper) is tracked separately as SOTA-A3.
"""

from __future__ import annotations

import os

import pytest

IDS_SCHEMA_FETCH_TIMEOUT_SECONDS = 10


def _prewarm_ifctester_schema() -> None:
    try:
        import ifctester.ids as ids_module
        from xmlschema import XMLSchema
    except ImportError:
        return
    if getattr(ids_module, "schema", None) is not None:
        return
    xsd = os.path.join(ids_module.cwd, "ids.xsd")
    ids_module.schema = XMLSchema(xsd, timeout=IDS_SCHEMA_FETCH_TIMEOUT_SECONDS)


def pytest_sessionstart(session: pytest.Session) -> None:
    # Collection-only runs (for example the runtime-baseline exporter's test
    # inventory subprocess) never open an IDS file; skip the network attempt.
    if session.config.option.collectonly:
        return
    _prewarm_ifctester_schema()
