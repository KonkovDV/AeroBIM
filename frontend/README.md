# Frontend Review Shell

The frontend is now an active browser review surface for persisted AeroBIM reports.

Current scope:

- report list with pass/fail and issue counts;
- report summary and export actions;
- issue detail panel with provenance fields;
- report-scoped IFC loading through the backend;
- initial 3D viewer with issue highlight / isolate by IFC GUID;
- provenance view for requirements, drawing annotations, and clashes.

## Stack

- React 19 + TypeScript
- Vite
- Three.js
- web-ifc
- CSS-only layout system for a lightweight standalone shell around the spatial review rail

## Run

```bash
cd frontend
npm install
npm run dev
```

Default API target: `http://localhost:8080`.

Override with:

```bash
VITE_AEROBIM_API_BASE_URL=http://localhost:8080
```

## Current Gaps

- no 2D raster/PDF overlay rendering yet;
- no clash-pair dual-selection workflow yet;
- no authoring-tool roundtrip yet.
