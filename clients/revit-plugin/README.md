# Revit thin client — package export + report deep-link

Boundary: **no validation logic in Revit**. The add-in (or this helper) only:

1. assembles a project package (IFC + optional IDS/specs paths);
2. calls AeroBIM `POST /v1/analyze/project-package`;
3. opens the review UI with `?report={report_id}`.

## Quick path (no Revit API required)

```powershell
cd clients/revit-plugin
python scripts/export_and_open_report.py `
  --api-base http://127.0.0.1:8080 `
  --ui-base http://127.0.0.1:5173 `
  --ifc C:\models\pilot.ifc `
  --ids C:\models\pilot.ids `
  --project "Pilot Tower" `
  --bearer $env:AEROBIM_API_BEARER_TOKEN
```

The script prints a deep-link URL and optionally opens the default browser.

## Deep-link contract

| Query param | Effect |
|-------------|--------|
| `report` | Select this report id in the review shell |
| `project` / `discipline` / `status` | Existing list filters (optional) |

## First plugin milestones (unchanged)

1. sign-in and project binding  
2. issue list pull  
3. element focus / isolate  
4. status and comment pushback  
5. BCF-linked roundtrip where applicable  

Validation and report truth stay in the backend.
