"""Deterministic synthetic project-package scaffold (fixture-grade, not customer)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SyntheticProjectPackage:
    project_id: str = "synthetic-residential-001"
    disciplines: tuple[str, ...] = ("AR", "KR", "MEP")
    ifc_schema: str = "IFC4"
    building_storeys: int = 3
    spaces: int = 12
    walls: int = 40
    doors: int = 15
    slabs: int = 8
    mep_elements: int = 30
    expected_defects: tuple[str, ...] = (
        "missing_property",
        "quantity_mismatch",
        "unit_mismatch",
        "geometry_clash",
        "missing_element",
        "revision_change",
        "cross_document_mismatch",
    )
    seed: int = 20260731


@dataclass
class MutationRecord:
    defect_id: str
    mutation_type: str
    source_asset: str
    target_guid: str | None
    expected_finding_kind: str
    expected_severity: str
    expected_evidence_refs: list[str] = field(default_factory=list)
    expected_status: str = "finding"
    input_hash: str = ""
    output_hash: str = ""
    seed: int = 0


def _minimal_ifc(*, project_id: str, discipline: str, seed: int) -> str:
    # Minimal STEP header + one IfcProject marker — not a full geometric model.
    return (
        "ISO-10303-21;\n"
        "HEADER;\n"
        f"FILE_NAME('{project_id}-{discipline}.ifc','',('AeroBIM'),('synthetic'),"
        f"'synthetic-generator','AeroBIM','');\n"
        "FILE_SCHEMA(('IFC4'));\n"
        "ENDSEC;\n"
        "DATA;\n"
        f"#1=IFCPROJECT('{discipline}{seed:04d}',$,'{project_id} {discipline}',$,$,$,$);\n"
        "ENDSEC;\n"
        "END-ISO-10303-21;\n"
    )


def generate_synthetic_package(
    out_dir: Path,
    *,
    package: SyntheticProjectPackage | None = None,
) -> dict[str, Any]:
    """Write synthetic package files + mutation SSOT. Never mutates repo samples/."""

    pkg = package or SyntheticProjectPackage()
    out_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    for discipline in pkg.disciplines:
        rel = f"ifc/{pkg.project_id}-{discipline.lower()}.ifc"
        content = _minimal_ifc(project_id=pkg.project_id, discipline=discipline, seed=pkg.seed)
        path = out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        files[rel] = hashlib.sha256(content.encode("utf-8")).hexdigest()

    ids_rel = f"ids/{pkg.project_id}.ids"
    ids_body = (
        '<?xml version="1.0"?><ids xmlns="http://standards.buildingsmart.org/IDS">'
        f"<info><title>{pkg.project_id}</title></info></ids>\n"
    )
    (out_dir / ids_rel).parent.mkdir(parents=True, exist_ok=True)
    (out_dir / ids_rel).write_text(ids_body, encoding="utf-8")
    files[ids_rel] = hashlib.sha256(ids_body.encode("utf-8")).hexdigest()

    mutations: list[MutationRecord] = []
    for index, defect in enumerate(pkg.expected_defects, start=1):
        source = next(iter(files))
        input_hash = files[source]
        mutations.append(
            MutationRecord(
                defect_id=f"SYN-{index:03d}",
                mutation_type=defect,
                source_asset=source,
                target_guid=None,
                expected_finding_kind=f"SYNTHETIC-{defect.upper()}",
                expected_severity="warning",
                expected_evidence_refs=[source],
                expected_status="finding",
                input_hash=input_hash,
                output_hash=hashlib.sha256(
                    f"{pkg.seed}:{defect}:{input_hash}".encode()
                ).hexdigest(),
                seed=pkg.seed + index,
            )
        )

    manifest = {
        "artifact_type": "synthetic_project_package",
        "claim_level": "synthetic_only",
        "customer_evidence": False,
        "package": asdict(pkg),
        "files": files,
        "mutations": [asdict(item) for item in mutations],
        "note": (
            "Synthetic scaffold for generator determinism tests. "
            "Not a substitute for public openBIM models or customer corpus."
        ),
    }
    (out_dir / "package-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


__all__ = [
    "MutationRecord",
    "SyntheticProjectPackage",
    "generate_synthetic_package",
]
