"""Node requirement must agree across .nvmrc, engines, CI and docs (AER-10).

The floor is 22.22.2: after jsdom 30, @asamuzakjp/css-color requires
``^22.22.2 || ^24.15.0 || >=26.0.0`` and ``engine-strict=true`` makes ``npm ci``
fail below it.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _checker():
    spec = importlib.util.spec_from_file_location(
        "check_node_versions", _REPO / "scripts" / "check_node_versions.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_nvmrc_engines_ci_and_docs_agree_on_node_22_22_2() -> None:
    assert (_REPO / ".nvmrc").read_text(encoding="utf-8").strip() == "22.22.2"
    assert (_REPO / ".node-version").read_text(encoding="utf-8").strip() == "22.22.2"
    engines = json.loads((_REPO / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert engines["engines"]["node"] == "^22.22.2 || ^24.15.0 || >=26.0.0"
    for wf in sorted((_REPO / ".github" / "workflows").glob("*.yml")):
        text = wf.read_text(encoding="utf-8")
        if "actions/setup-node" in text:
            assert "node-version-file: .nvmrc" in text, wf.name
            assert not re.search(r"node-version:\s", text), wf.name
    for doc in ("README.md", "README.ru.md", "frontend/README.md"):
        text = (_REPO / doc).read_text(encoding="utf-8")
        assert "Node 22.22.2+" in text, doc
        assert "Node 22.12+" not in text, doc
        assert "Node 20+" not in text, doc


def test_repo_wide_node_consistency_check_passes() -> None:
    assert _checker().check() == []


def test_checker_rejects_a_floor_below_a_dependency_engine() -> None:
    checker = _checker()
    floor = checker.parse_version("22.20.0")
    assert not checker.satisfies(floor, "^22.22.2 || ^24.15.0 || >=26.0.0")
    assert checker.satisfies(checker.parse_version("22.22.2"), "^22.22.2 || ^24.15.0 || >=26.0.0")
    assert checker.satisfies(checker.parse_version("22.22.2"), "^20.19.0 || >=22.12.0")
    assert not checker.satisfies(checker.parse_version("24.0.0"), "^22.22.2 || ^24.15.0")
    assert checker.floor_of("^22.22.2 || ^24.15.0 || >=26.0.0") == (22, 22, 2)
