"""WP-06: run open-corpora measurability profiles (regression / pilot-approx / load).

Open sets lack expert TP/FP labels → regression and timing only, never product
accuracy and never a >90% claim. Artifacts land under ``artifacts/open-corpora/``
with input/output SHA pins and an explicit claim_boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import RequirementSource, SourceKind, ValidationRequest
from aerobim.infrastructure.adapters.json_section_diff_analyzer import JsonSectionDiffAnalyzer
from aerobim.infrastructure.di.bootstrap import bootstrap_container

CLAIM_BOUNDARY = (
    "Open sets lack expert TP/FP labels -> regression/timing only, "
    "NOT product accuracy. Never claim >90%."
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_profiles_dir() -> Path:
    return repo_root() / "samples" / "benchmarks" / "open-corpora" / "profiles"


def default_output_dir() -> Path:
    return repo_root() / "artifacts" / "open-corpora"


def sha256_file(path: Path) -> str:
    """Hash bytes as committed on Linux CI (LF text), matching samples manifest."""

    data = path.read_bytes()
    if b"\r\n" in data and b"\x00" not in data[:8192]:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _resolve(repo: Path, rel: str) -> Path:
    path = (repo / rel).resolve()
    if not path.is_relative_to(repo.resolve()):
        raise ValueError(f"path escapes repo root: {rel}")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must be a JSON object")
    return payload


def verify_pin(path: Path, expected_sha256: str) -> dict[str, object]:
    actual = sha256_file(path)
    return {
        "path": str(path.as_posix()),
        "expected_sha256": expected_sha256,
        "actual_sha256": actual,
        "ok": actual == expected_sha256,
    }


def verify_regression_pins(
    profile: dict[str, Any],
    *,
    repo: Path,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for case in profile.get("cases") or []:
        if not isinstance(case, dict):
            raise ValueError("regression case must be an object")
        pins = case.get("pins") or {}
        results.append(
            {
                "case_id": case.get("case_id"),
                "ids": verify_pin(_resolve(repo, str(case["ids_path"])), str(pins["ids_sha256"])),
                "ifc": verify_pin(_resolve(repo, str(case["ifc_path"])), str(pins["ifc_sha256"])),
            }
        )
    return results


def verify_pilot_approx_pins(
    profile: dict[str, Any],
    *,
    repo: Path,
) -> list[dict[str, object]]:
    request = profile.get("request") or {}
    pins = profile.get("pins") or {}
    checks = [
        ("ifc", str(request["ifc_path"]), str(pins["ifc_sha256"])),
        ("requirement", str(request["requirement_path"]), str(pins["requirement_sha256"])),
        (
            "package_inventory",
            str(request["package_inventory_path"]),
            str(pins["package_inventory_sha256"]),
        ),
    ]
    secondary = profile.get("secondary_public_ifc")
    if isinstance(secondary, dict):
        checks.append(("secondary_ifc", str(secondary["path"]), str(secondary["sha256"])))
    return [
        {"role": role, **verify_pin(_resolve(repo, rel), expected)}
        for role, rel, expected in checks
    ]


def verify_load_pins(
    profile: dict[str, Any],
    *,
    repo: Path,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for pair in profile.get("section_pairs") or []:
        if not isinstance(pair, dict):
            raise ValueError("section_pair must be an object")
        pins = pair.get("pins") or {}
        results.append(
            {
                "pair_id": pair.get("pair_id"),
                "pd": verify_pin(
                    _resolve(repo, str(pair["pd_section_path"])), str(pins["pd_sha256"])
                ),
                "rd": verify_pin(
                    _resolve(repo, str(pair["rd_section_path"])), str(pins["rd_sha256"])
                ),
            }
        )
    mep = profile.get("mep_pack") or {}
    if isinstance(mep, dict) and mep:
        pins = mep.get("pins") or {}
        results.append(
            {
                "pack_id": mep.get("pack_id"),
                "ifc": verify_pin(_resolve(repo, str(mep["ifc_path"])), str(pins["ifc_sha256"])),
                "requirement": verify_pin(
                    _resolve(repo, str(mep["requirement_path"])),
                    str(pins["requirement_sha256"]),
                ),
                "mep_federated_scope": verify_pin(
                    _resolve(repo, str(mep["mep_federated_scope_path"])),
                    str(pins["mep_federated_scope_sha256"]),
                ),
            }
        )
    return results


def all_pins_ok(pin_results: list[dict[str, object]]) -> bool:
    """Walk nested pin verification rows; any ``ok: False`` fails the smoke."""

    stack: list[object] = list(pin_results)
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if "ok" in item and item["ok"] is False:
                return False
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return True


def _bootstrap_use_case(storage_dir: Path, *, mep_scope: Path | None = None) -> tuple[Any, Any]:
    settings = Settings(
        application_name="aerobim-open-corpora",
        environment="test",
        host="127.0.0.1",
        port=8080,
        storage_dir=storage_dir,
        debug=True,
        mep_federated_scope_path=str(mep_scope) if mep_scope else None,
    )
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    container = bootstrap_container(settings)
    return container.resolve(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE), container.resolve(
        Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE
    )


def run_regression_profile(
    profile: dict[str, Any],
    *,
    repo: Path,
    storage_dir: Path,
) -> dict[str, Any]:
    pin_results = verify_regression_pins(profile, repo=repo)
    if not all_pins_ok(pin_results):
        raise ValueError("regression profile pin mismatch — refuse to run")

    validate_uc, _ = _bootstrap_use_case(storage_dir)
    case_rows: list[dict[str, object]] = []
    matched = 0
    for case in profile["cases"]:
        assert isinstance(case, dict)
        ids_path = _resolve(repo, str(case["ids_path"]))
        ifc_path = _resolve(repo, str(case["ifc_path"]))
        expected = bool(case["expected_passed"])
        started = perf_counter()
        report = validate_uc.execute(
            ValidationRequest(
                request_id=f"open-corpora-reg-{case['case_id']}",
                ifc_path=ifc_path,
                requirement_source=RequirementSource(
                    text="",
                    source_kind=SourceKind.STRUCTURED_TEXT,
                    source_id="open-corpora-empty",
                ),
                ids_path=ids_path,
                origin="open-corpora-regression",
            )
        )
        elapsed_ms = round((perf_counter() - started) * 1000.0, 3)
        actual = bool(report.summary.passed)
        ok = actual == expected
        if ok:
            matched += 1
        case_rows.append(
            {
                "case_id": case["case_id"],
                "expected_passed": expected,
                "actual_passed": actual,
                "match": ok,
                "issue_count": report.summary.issue_count,
                "elapsed_ms": elapsed_ms,
            }
        )

    total = len(case_rows)
    return {
        "profile_id": profile["profile_id"],
        "profile_kind": "regression",
        "honest_case_count": int(profile.get("honest_case_count") or total),
        "cases_run": total,
        "cases_matched": matched,
        "binary_match_rate": round(matched / total, 6) if total else 0.0,
        "cases": case_rows,
        "input_pins": pin_results,
        "claim_boundary": CLAIM_BOUNDARY,
        "note": ("binary_match_rate is fixture regression fidelity, not product precision"),
    }


def run_pilot_approx_profile(
    profile: dict[str, Any],
    *,
    repo: Path,
    storage_dir: Path,
) -> dict[str, Any]:
    pin_results = verify_pilot_approx_pins(profile, repo=repo)
    if not all_pins_ok(pin_results):
        raise ValueError("pilot-approx profile pin mismatch — refuse to run")

    request_data = profile["request"]
    assert isinstance(request_data, dict)
    ifc_path = _resolve(repo, str(request_data["ifc_path"]))
    requirement_path = _resolve(repo, str(request_data["requirement_path"]))
    inventory_path = _resolve(repo, str(request_data["package_inventory_path"]))
    _, analyze_uc = _bootstrap_use_case(storage_dir)

    iterations = max(1, int(profile.get("iterations") or 1))
    warmup = max(0, int(profile.get("warmup_iterations") or 0))
    base = ValidationRequest(
        request_id="open-corpora-pilot-approx",
        ifc_path=ifc_path,
        requirement_source=RequirementSource(
            text=requirement_path.read_text(encoding="utf-8"),
            path=requirement_path,
            source_kind=SourceKind.STRUCTURED_TEXT,
            source_id="open-corpora-pilot-approx-req",
        ),
        package_inventory_path=inventory_path,
        require_package_completeness=bool(request_data.get("require_package_completeness", True)),
        origin="open-corpora-pilot-approx",
        project_name="open-corpora-pilot-approx",
        discipline="architecture",
    )

    for index in range(1, warmup + 1):
        analyze_uc.execute(replace(base, request_id=f"{base.request_id}-warmup-{index:03d}"))

    measured: list[dict[str, object]] = []
    for index in range(1, iterations + 1):
        req = replace(base, request_id=f"{base.request_id}-run-{index:03d}")
        started = perf_counter()
        report = analyze_uc.execute(req)
        elapsed_ms = round((perf_counter() - started) * 1000.0, 3)
        measured.append(
            {
                "iteration": index,
                "elapsed_ms": elapsed_ms,
                "report_id": report.report_id,
                "issue_count": report.summary.issue_count,
                "passed": report.summary.passed,
            }
        )

    elapsed_values = [
        float(row["elapsed_ms"]) for row in measured if isinstance(row["elapsed_ms"], (int, float))
    ]
    return {
        "profile_id": profile["profile_id"],
        "profile_kind": "pilot_approx",
        "iterations": iterations,
        "warmup_iterations": warmup,
        "measured_runs": measured,
        "summary": {
            "min_ms": round(min(elapsed_values), 3),
            "max_ms": round(max(elapsed_values), 3),
            "avg_ms": round(sum(elapsed_values) / len(elapsed_values), 3),
        },
        "input_pins": pin_results,
        "claim_boundary": CLAIM_BOUNDARY,
        "note": "package analyze timing on public IFC + residential inventory; not customer SLA",
    }


def run_load_profile(
    profile: dict[str, Any],
    *,
    repo: Path,
    storage_dir: Path,
) -> dict[str, Any]:
    pin_results = verify_load_pins(profile, repo=repo)
    if not all_pins_ok(pin_results):
        raise ValueError("load profile pin mismatch — refuse to run")

    analyzer = JsonSectionDiffAnalyzer()
    pair_rows: list[dict[str, object]] = []
    for pair in profile.get("section_pairs") or []:
        assert isinstance(pair, dict)
        pd_path = _resolve(repo, str(pair["pd_section_path"]))
        rd_path = _resolve(repo, str(pair["rd_section_path"]))
        started = perf_counter()
        report = analyzer.analyze(pd_path, rd_path)
        elapsed_ms = round((perf_counter() - started) * 1000.0, 3)
        pair_rows.append(
            {
                "pair_id": pair["pair_id"],
                "discipline": pair.get("discipline"),
                "elapsed_ms": elapsed_ms,
                "issue_count": len(report.issues),
                "recognized_key_count": report.recognized_key_count,
                "capability_reason": report.capability_reason(pd_path.name, rd_path.name),
            }
        )

    mep_row: dict[str, object] | None = None
    mep = profile.get("mep_pack")
    if isinstance(mep, dict) and mep:
        scope_rel = str(mep["mep_federated_scope_path"])
        _resolve(repo, scope_rel)  # pin/existence gate before analyze
        _, analyze_uc = _bootstrap_use_case(storage_dir, mep_scope=Path(scope_rel))
        ifc_path = _resolve(repo, str(mep["ifc_path"]))
        requirement_path = _resolve(repo, str(mep["requirement_path"]))
        req = ValidationRequest(
            request_id="open-corpora-load-mep",
            ifc_path=ifc_path,
            requirement_source=RequirementSource(
                text=requirement_path.read_text(encoding="utf-8"),
                path=requirement_path,
                source_kind=SourceKind.STRUCTURED_TEXT,
                source_id="open-corpora-load-mep-req",
            ),
            origin="open-corpora-load",
            project_name="open-corpora-load-mep",
            discipline="mep",
        )
        started = perf_counter()
        report = analyze_uc.execute(req)
        elapsed_ms = round((perf_counter() - started) * 1000.0, 3)
        mep_row = {
            "pack_id": mep.get("pack_id"),
            "elapsed_ms": elapsed_ms,
            "report_id": report.report_id,
            "issue_count": report.summary.issue_count,
            "note": mep.get("note"),
        }

    return {
        "profile_id": profile["profile_id"],
        "profile_kind": "load",
        "section_pairs": pair_rows,
        "mep_pack": mep_row,
        "input_pins": pin_results,
        "claim_boundary": CLAIM_BOUNDARY,
        "note": (
            "cross-doc (AR/KZH pairing) + MEP federated path timing; never mep_system_clash=OK"
        ),
    }


def run_smoke(
    *,
    repo: Path,
    profiles_dir: Path,
) -> dict[str, Any]:
    """Cheap CI smoke: load profiles and verify SHA pins only."""

    regression = _load_json(profiles_dir / "regression.json")
    pilot = _load_json(profiles_dir / "pilot-approx.json")
    load = _load_json(profiles_dir / "load.json")
    pin_blocks = {
        "regression": verify_regression_pins(regression, repo=repo),
        "pilot_approx": verify_pilot_approx_pins(pilot, repo=repo),
        "load": verify_load_pins(load, repo=repo),
    }
    ok = all(all_pins_ok(rows) for rows in pin_blocks.values())
    return {
        "mode": "smoke",
        "pins_ok": ok,
        "honest_regression_case_count": int(regression.get("honest_case_count") or 0),
        "profiles": pin_blocks,
        "claim_boundary": CLAIM_BOUNDARY,
        "note": "smoke verifies SHA pins only; full IDS/analyze is manual or --mode full",
    }


def run_all_profiles(
    *,
    repo: Path | None = None,
    profiles_dir: Path | None = None,
    output_dir: Path | None = None,
    mode: str = "full",
) -> dict[str, Any]:
    resolved_repo = (repo or repo_root()).resolve()
    resolved_profiles = (profiles_dir or default_profiles_dir()).resolve()
    resolved_output = (output_dir or default_output_dir()).resolve()
    resolved_output.mkdir(parents=True, exist_ok=True)

    if mode == "smoke":
        artifact = {
            "artifact_type": "open_corpora_profiles_run",
            "schema_version": "1.0.0",
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "claim_boundary": CLAIM_BOUNDARY,
            **run_smoke(repo=resolved_repo, profiles_dir=resolved_profiles),
        }
    elif mode == "full":
        with tempfile.TemporaryDirectory(prefix="aerobim-open-corpora-") as tmp:
            storage = Path(tmp) / "var"
            regression = run_regression_profile(
                _load_json(resolved_profiles / "regression.json"),
                repo=resolved_repo,
                storage_dir=storage / "regression",
            )
            pilot = run_pilot_approx_profile(
                _load_json(resolved_profiles / "pilot-approx.json"),
                repo=resolved_repo,
                storage_dir=storage / "pilot",
            )
            load = run_load_profile(
                _load_json(resolved_profiles / "load.json"),
                repo=resolved_repo,
                storage_dir=storage / "load",
            )
        artifact = {
            "artifact_type": "open_corpora_profiles_run",
            "schema_version": "1.0.0",
            "mode": "full",
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "claim_boundary": CLAIM_BOUNDARY,
            "profiles": {
                "regression": regression,
                "pilot_approx": pilot,
                "load": load,
            },
        }
    else:
        raise ValueError(f"unknown mode {mode!r}; use smoke|full")

    rendered = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"
    output_bytes = rendered.encode("utf-8")
    output_hash = sha256_bytes(output_bytes)
    artifact["output_sha256"] = output_hash
    rendered = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"

    out_path = resolved_output / f"open-corpora-{mode}.json"
    out_path.write_text(rendered, encoding="utf-8")
    summary_path = resolved_output / "README.md"
    summary_path.write_text(
        "\n".join(
            [
                "# Open corpora run artifacts (WP-06)",
                "",
                f"- mode: `{mode}`",
                f"- output: `{out_path.name}`",
                f"- output_sha256: `{output_hash}`",
                f"- claim_boundary: {CLAIM_BOUNDARY}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    artifact["output_path"] = str(out_path.as_posix())
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("smoke", "full"),
        default="full",
        help="smoke = pin verification only; full = live IDS/analyze/timing",
    )
    parser.add_argument("--profiles-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)

    artifact = run_all_profiles(
        repo=args.repo_root,
        profiles_dir=args.profiles_dir,
        output_dir=args.output_dir,
        mode=args.mode,
    )
    print(json.dumps(artifact, ensure_ascii=False, indent=2))
    if args.mode == "smoke" and not artifact.get("pins_ok", False):
        return 2
    if args.mode == "full":
        regression = (artifact.get("profiles") or {}).get("regression") or {}
        if regression.get("cases_matched") != regression.get("cases_run"):
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
