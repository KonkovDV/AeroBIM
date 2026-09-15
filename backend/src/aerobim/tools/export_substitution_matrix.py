"""Classify DI tokens as live adapter / in_memory / missing (stubs count as missing).

Percent of Tokens members, not a buy-vs-build quote. Checkpoint GO; customer_go false.
Not registered in the operator catalog (cap ≤40).
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.checkpoint import CHECKPOINT, checkpoint_fields
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools._cli_base import run_cli
from aerobim.tools.export_runtime_baseline import _live_architecture_inventory

_IN_MEMORY_MARKERS = ("InMemory", "in_memory")
_MISSING_MARKERS = (
    "Stub",
    "Unconfigured",
    "Disabled",
    "NotImplemented",
    "Missing",
    "NullAdapter",
    "NoOp",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def token_names() -> tuple[str, ...]:
    names = [
        name for name, value in vars(Tokens).items() if name.isupper() and isinstance(value, str)
    ]
    return tuple(sorted(names))


def _classify_source(source: str) -> str:
    if any(marker in source for marker in _IN_MEMORY_MARKERS):
        return "in_memory"
    if any(marker in source for marker in _MISSING_MARKERS):
        return "missing"
    return "live_adapter"


def classify_tokens() -> dict[str, object]:
    with TemporaryDirectory(prefix="aerobim-subst-") as tmp:
        settings = Settings(
            application_name="aerobim-substitution-matrix",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path(tmp) / "var",
            debug=True,
        )
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        container = bootstrap_container(settings)
        rows: list[dict[str, str]] = []
        for name in token_names():
            token = getattr(Tokens, name)
            if not container.is_registered(token):
                rows.append({"token": token, "name": name, "kind": "missing"})
                continue
            try:
                instance = container.resolve(token)
            except Exception as exc:
                rows.append(
                    {
                        "token": token,
                        "name": name,
                        "kind": "missing",
                        "error": f"{type(exc).__name__}: {exc}"[:200],
                    }
                )
                continue
            cls_name = type(instance).__name__
            module = type(instance).__module__
            kind = _classify_source(f"{module}.{cls_name}")
            if name in {"SETTINGS", "LOGGER"}:
                kind = "live_adapter"
            rows.append(
                {
                    "token": token,
                    "name": name,
                    "kind": kind,
                    "class_name": cls_name,
                }
            )
    counts = {"live_adapter": 0, "in_memory": 0, "missing": 0}
    for row in rows:
        counts[row["kind"]] += 1
    total = len(rows)
    percents = {
        key: round(100.0 * value / total, 1) if total else 0.0 for key, value in counts.items()
    }
    return {
        "token_count": total,
        "counts": counts,
        "percents": percents,
        "rows": rows,
    }


def build_payload(*, generated_at: str | None = None) -> dict[str, object]:
    classified = classify_tokens()
    inventory = _live_architecture_inventory(repo_root())
    payload: dict[str, object] = {
        "schema_version": "1.0.0",
        "artifact_type": "aerobim_substitution_matrix",
        "claim_level": "code_inventory",
        "claim_boundary": (
            "Classification of resolved instance class names at test bootstrap. "
            "Stubs/Unconfigured/Disabled map to missing. InMemory* maps to in_memory. "
            "Not a vendor quote. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
        ),
    }
    payload.update(checkpoint_fields())
    payload.update(
        {
            "generated_at": generated_at or datetime.now(tz=UTC).isoformat(),
            "closes_rt001": False,
            "architecture_inventory": inventory,
            "di_tokens_expected": inventory["di_tokens"],
            "classified": classified,
            "checkpoint": CHECKPOINT,
        }
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--write-docs-evidence", action="store_true")
    args = parser.parse_args(argv)
    payload = build_payload()
    classified = payload["classified"]
    assert isinstance(classified, dict)
    if int(classified["token_count"]) != int(payload["di_tokens_expected"]):
        raise SystemExit(
            f"token_count {classified['token_count']} != "
            f"architecture_inventory.di_tokens {payload['di_tokens_expected']}"
        )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    root = repo_root()
    out = args.output
    if args.write_docs_evidence:
        out = root / "docs" / "evidence" / "substitution-matrix-latest.json"
    if out is None:
        raise SystemExit("pass --output or --write-docs-evidence")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")
    print(json.dumps({"percents": classified["percents"], "counts": classified["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(lambda: main()))
