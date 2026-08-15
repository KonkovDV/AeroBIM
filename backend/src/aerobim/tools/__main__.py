"""List active operator CLI tools: ``python -m aerobim.tools``."""

from __future__ import annotations

import json

from aerobim.tools.tool_catalog import active_tools, catalog


def main() -> int:
    payload = {
        "artifact_type": "aerobim_tool_catalog",
        "schema_version": "1.0.0",
        "active": list(active_tools()),
        "groups": {name: list(names) for name, names in catalog().items()},
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
