"""Shared CLI helpers for operator tools (no behaviour change required)."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container
from aerobim.infrastructure.di.bootstrap import bootstrap_container

__all__ = [
    "add_common_args",
    "bootstrap_container",
    "container_from_env",
    "output_json",
    "run_cli",
]

JsonDict = dict[str, Any]


def add_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON on stdout (default for most tools)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra diagnostics to stderr",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON to this path instead of stdout",
    )
    return parser


def output_json(data: JsonDict, path: Path | None = None) -> None:
    serialized = json.dumps(data, ensure_ascii=False, indent=2)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized + "\n", encoding="utf-8")
        return
    print(serialized)


def container_from_env(*, storage_dir: Path | None = None) -> Container:
    settings = Settings.from_env()
    if storage_dir is not None:
        from dataclasses import replace

        settings = replace(settings, storage_dir=storage_dir.resolve())
    return bootstrap_container(settings)


def run_cli(fn: Callable[[], int | None]) -> int:
    """Run a tool main and map exceptions to exit codes."""

    try:
        result = fn()
    except BrokenPipeError:
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0 if result is None else int(result)
