"""Native DWG toolchain health check — honesty probe, never a DWG-ready claim.

Reports whether ezdxf, ODA legal gate, and optional converters are present.
``native_dwg`` stays missing until a licensed ODA/Teigha SDK is wired (STUB-ODA-CAD-001).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from aerobim.core.config.settings import Settings
from aerobim.domain.cad_ingest import NATIVE_DWG_MISSING_REASON
from aerobim.infrastructure.adapters.oda_cad_model_ingestor import OdaCadModelIngestor

_CONVERTER_CANDIDATES = (
    "ODAFileConverter",
    "TeighaFileConverter",
    "dwg2dxf",
    "LibreDWG",
    "dwgread",
)


def probe_dwg_toolchain(*, settings: Settings | None = None) -> dict[str, Any]:
    """Return a fail-closed snapshot of DWG-related tooling."""

    runtime = settings or Settings.from_env()
    ezdxf_present = find_spec("ezdxf") is not None
    converters = {name: bool(shutil.which(name)) for name in _CONVERTER_CANDIDATES}
    oda = OdaCadModelIngestor(enabled=runtime.oda_cad_enabled)
    ingest = oda.ingest(Path("probe.dwg"))
    return {
        "artifact_type": "dwg_toolchain_probe",
        "schema_version": "1.0.0",
        "native_dwg": "missing",
        "dwg_native": "NOT_IMPLEMENTED",
        "claim_allowed": False,
        "oda_cad_enabled": runtime.oda_cad_enabled,
        "oda_sdk_present": False,
        "oda_ingest_supported": ingest.supported,
        "oda_reason": ingest.reason,
        "ezdxf_present": ezdxf_present,
        "dxf_path": "partial" if ezdxf_present else "skipped",
        "converters_on_path": converters,
        "any_converter": any(converters.values()),
        "reason": NATIVE_DWG_MISSING_REASON,
        "claim_boundary": (
            "DXF via optional ezdxf is not native DWG. ODA legal gate open ≠ SDK present. "
            "Never dwg_supported / DWG-ready."
        ),
        "stub_id": "STUB-ODA-CAD-001",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON snapshot (stdout when omitted)",
    )
    args = parser.parse_args(argv)
    payload = probe_dwg_toolchain()
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
