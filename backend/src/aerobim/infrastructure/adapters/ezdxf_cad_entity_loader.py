"""CadEntityLoaderPort — full ezdxf EntityGraph (objects / dimensions / text).

Optional extra ``aerobim-backend[cad]``. Native DWG requires ODA port (legal flag).
``ReportCapabilities.dwg_dxf`` must never become OK (honesty).
"""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.models import CapabilityState, CapabilityStatus
from aerobim.domain.tz_architecture_ports import CadEntity, EntityGraph

_DXF = {".dxf"}
_DWG = {".dwg"}
_TEXT_TYPES = {"TEXT", "MTEXT"}
_DIM_TYPES = {"DIMENSION", "ALIGNED_DIMENSION", "LINEAR_DIMENSION", "ORDINATE_DIMENSION"}
_GEOM_TYPES = {"LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC", "INSERT", "HATCH"}


class EzdxfCadEntityLoader:
    """Combat DXF backend → EntityGraph (IFC-analog contract for overlays).

    When ``ezdxf`` is absent, returns ``capability=SKIPPED`` (not silent OK).
    """

    def load(self, path: Path) -> EntityGraph:
        if not path.exists():
            raise FileNotFoundError(path)

        suffix = path.suffix.lower()
        if suffix in _DWG:
            return EntityGraph(
                source_id=path.name,
                format="dwg",
                entities=(),
                capability=CapabilityStatus(
                    status=CapabilityState.NOT_VERIFIED,
                    reason=(
                        "Native DWG requires ODA/Teigha adapter behind legal review "
                        "(AEROBIM_ODA_CAD_ENABLED); convert to DXF or enable ODA port"
                    ),
                ),
            )

        if suffix not in _DXF:
            return EntityGraph(
                source_id=path.name,
                format="unknown",
                entities=(),
                capability=CapabilityStatus(
                    status=CapabilityState.SKIPPED,
                    reason=f"Unsupported CAD suffix {suffix!r}; expected .dxf or .dwg",
                ),
            )

        try:
            import ezdxf
        except ModuleNotFoundError:
            return EntityGraph(
                source_id=path.name,
                format="dxf",
                entities=(),
                capability=CapabilityStatus(
                    status=CapabilityState.SKIPPED,
                    reason="ezdxf optional extra not installed (pip install aerobim-backend[cad])",
                ),
            )

        try:
            document = ezdxf.readfile(str(path))
        except Exception as exc:  # noqa: BLE001
            return EntityGraph(
                source_id=path.name,
                format="dxf",
                entities=(),
                capability=CapabilityStatus(
                    status=CapabilityState.FAILED,
                    reason=f"ezdxf failed to read DXF: {exc}",
                ),
            )

        entities: list[CadEntity] = []
        for index, entity in enumerate(document.modelspace()):
            dxftype = entity.dxftype()
            layer = str(getattr(entity.dxf, "layer", "") or "") or None
            entity_id = f"dxf-{path.stem}-{index}-{dxftype}"
            if dxftype in _TEXT_TYPES:
                text = ""
                if dxftype == "TEXT":
                    text = str(getattr(entity.dxf, "text", "") or "").strip()
                    insert = getattr(entity.dxf, "insert", None)
                else:
                    text = str(entity.plain_text() if hasattr(entity, "plain_text") else "").strip()
                    insert = getattr(entity.dxf, "insert", None)
                if not text:
                    continue
                bbox = (
                    (float(insert[0]), float(insert[1]), float(insert[0]), float(insert[1]))
                    if insert is not None
                    else None
                )
                entities.append(
                    CadEntity(
                        entity_id=entity_id,
                        kind="annotation_text",
                        layer=layer,
                        attributes={"text": text, "dxftype": dxftype},
                        bbox=bbox,
                    )
                )
            elif dxftype in _DIM_TYPES or "DIMENSION" in dxftype:
                measurement = ""
                if hasattr(entity, "get_measurement"):
                    try:
                        measurement = str(entity.get_measurement())
                    except Exception:  # noqa: BLE001
                        measurement = ""
                text_override = str(getattr(entity.dxf, "text", "") or "").strip()
                entities.append(
                    CadEntity(
                        entity_id=entity_id,
                        kind="dimension",
                        layer=layer,
                        attributes={
                            "dxftype": dxftype,
                            "measurement": measurement,
                            "text": text_override,
                        },
                    )
                )
            elif dxftype in _GEOM_TYPES:
                entities.append(
                    CadEntity(
                        entity_id=entity_id,
                        kind="geometry",
                        layer=layer,
                        attributes={"dxftype": dxftype},
                    )
                )

        return EntityGraph(
            source_id=path.name,
            format="dxf",
            entities=tuple(entities),
            capability=CapabilityStatus(
                status=CapabilityState.NOT_VERIFIED,
                reason=(
                    f"DXF EntityGraph via ezdxf: entities={len(entities)} "
                    "(objects/dimensions/annotations); report dwg_dxf never OK"
                ),
            ),
        )
