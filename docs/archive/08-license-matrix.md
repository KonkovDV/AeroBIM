# Open-Source License Matrix

Dependencies used by the AeroBIM BIM Compliance Engine, with license compatibility assessment.

| Package | License | Category | Constraints |
|---|---|---|---|
| **IfcOpenShell** 0.8.x | LGPL-3.0 | IFC parser + geometry | LGPL: dynamic linking OK, static linking requires source disclosure. No issue for a Python import. |
| **IfcTester** (ifcopenshell ecosystem) | LGPL-3.0 | IDS validation engine | Same LGPL terms as IfcOpenShell. Runs as a library call, no redistribution concern for SaaS. |
| **IfcClash** (ifcopenshell ecosystem) | LGPL-3.0 | Clash detection | Same terms. Optional runtime dependency. |
| **FastAPI** | MIT | HTTP framework | Permissive. No restrictions. |
| **Pydantic** v2 | MIT | Data validation | Permissive. |
| **Uvicorn** | BSD-3-Clause | ASGI server | Permissive. |
| **pytest** | MIT | Test framework | Dev-only dependency. |

## BIM Viewer Libraries (planned, not yet integrated)

| Package | License | Category | Constraints |
|---|---|---|---|
| **web-ifc** | MPL-2.0 | WASM IFC parser | File-level copyleft: modified files of web-ifc itself must remain MPL-2.0. Own code unaffected. Compatible with proprietary hosting. |
| **xeokit-sdk** | AGPL-3.0 / Commercial | 3D BIM viewer | **AGPL**: network use = distribution. SaaS deployment requires either (a) full source disclosure or (b) commercial license from xeokit BV. Evaluate commercial license before integration. |
| **Three.js** | MIT | 3D rendering | Permissive. Used by xeokit internally. |
| **IFC.js (That Open Company)** | AGPL-3.0 / Commercial | Alternative IFC tools | Same AGPL concern as xeokit. |
| **BIMserver** | AGPL-3.0 | Model server | AGPL: full source disclosure for network services. Not currently planned. |

## Compatibility Summary

- **Current stack** (IfcOpenShell + FastAPI): all LGPL/MIT/BSD — **fully compatible** with proprietary SaaS deployment.
- **xeokit integration**: requires commercial license evaluation if used in a non-open-source product. This is the primary licensing risk.
- **web-ifc**: MPL-2.0 is fine for SaaS as long as modifications to web-ifc files themselves are disclosed.

## Recommendation

1. Use IfcOpenShell stack as the primary backend — no licensing friction.
2. For the 3D viewer, prefer **web-ifc + Three.js** (MIT+MPL-2.0) over xeokit (AGPL) unless the commercial xeokit license is acquired.
3. Keep `ifcclash` as an optional dependency with graceful fallback.
