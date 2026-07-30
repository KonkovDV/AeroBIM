"""F-02 guard: the SLA artifact must surface package scale so a trivially small
pack cannot masquerade as a real-scale <=30 min SLA run (Red Team A2/A13)."""

from __future__ import annotations

from pathlib import Path

from aerobim.tools.measure_package_sla import (
    REPRESENTATIVE_MIN_INPUT_BYTES,
    measure_package_sla,
    package_scale,
)


def test_package_scale_flags_trivial_pack_as_not_representative() -> None:
    inventory = [
        {"path": "packs/tiny.json", "bytes": 1096},
        {"path": "samples/ifc/walls.ifc", "bytes": 4096},
    ]
    scale = package_scale(inventory, manifest={"request": {"drawings": [{"path": "d.txt"}]}})
    assert scale["is_representative"] is False
    assert scale["input_files"] == 1
    assert scale["drawing_count"] == 1


def test_package_scale_flags_large_multi_source_pack_as_representative() -> None:
    inventory = [
        {"path": "packs/big.json", "bytes": 2000},
        {"path": "samples/ifc/model.ifc", "bytes": REPRESENTATIVE_MIN_INPUT_BYTES + 1},
        {"path": "samples/req.txt", "bytes": 5000},
        {"path": "samples/calc.txt", "bytes": 5000},
    ]
    scale = package_scale(inventory, manifest={})
    assert scale["is_representative"] is True
    assert scale["input_files"] == 3
    assert int(scale["ifc_bytes"]) >= REPRESENTATIVE_MIN_INPUT_BYTES


def test_measure_sla_emits_package_scale_for_pilot_pack() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    pack = repo_root / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"
    result = measure_package_sla(pack, max_minutes=30.0, iterations=1, warmup_iterations=0)
    assert "package_scale" in result
    scale = result["package_scale"]
    assert isinstance(scale, dict)
    # The pilot fixture pack references only tiny fixtures -> not representative.
    assert result["representative_scale"] is False
    # request-nested inputs are now resolved into the inventory.
    assert int(scale["input_files"]) >= 1
