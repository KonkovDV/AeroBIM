"""Node requirement must agree across .nvmrc, engines, CI and docs (vitest 5 needs 22.12+)."""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def test_nvmrc_engines_ci_and_docs_agree_on_node_22_12() -> None:
    assert (_REPO / ".nvmrc").read_text(encoding="utf-8").strip() == "22"
    engines = json.loads((_REPO / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert engines["engines"]["node"] == ">=22.12"
    for wf in sorted((_REPO / ".github" / "workflows").glob("*.yml")):
        text = wf.read_text(encoding="utf-8")
        if "actions/setup-node" in text:
            assert "node-version-file: .nvmrc" in text, wf.name
            assert not re.search(r"node-version:\s", text), wf.name
    for doc in ("README.md", "README.ru.md", "frontend/README.md"):
        text = (_REPO / doc).read_text(encoding="utf-8")
        assert "Node 22.12+" in text, doc
        assert "Node 20+" not in text, doc
