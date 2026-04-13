# Frontend Review Shell

The frontend is now an active browser review surface for persisted AeroBIM reports.

Current scope:

- report list with pass/fail and issue counts;
- report summary and export actions;
- issue detail panel with provenance fields;
- report-scoped IFC loading through the backend;
- initial 3D viewer with issue highlight / isolate by IFC GUID;
- clash-pair focus and multi-selection isolate workflow in the viewer;
- 2D issue overlay panel backed by persisted drawing preview assets;
- drawing asset/page switching for report-level 2D evidence browsing;
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
npm test
npm run dev
npm run smoke:browser
```

Default API target: `http://localhost:8080`.

Override with:

```bash
VITE_AEROBIM_API_BASE_URL=http://localhost:8080
```

## Current Gaps

- no one-command browser harness that boots backend + seeding + frontend automatically yet;
- no authoring-tool roundtrip yet.

## Browser Smoke Capture

With the backend running, one deterministic smoke report seeded, and the frontend dev server available at `http://127.0.0.1:5173`, run:

```bash
cd frontend
npm run smoke:browser
```

The script captures:

- `artifacts/browser-smoke/review-shell-issue.png`
- `artifacts/browser-smoke/review-shell-clash.png`
- `artifacts/browser-smoke/review-shell-smoke.trace.zip`

In backend debug mode, the default CORS fallback now allows both `localhost` and `127.0.0.1` frontend dev origins for the standard local ports.

If Vite shifts to another port because `5173` is already taken, rerun the harness with the actual dev URL, for example `npm run smoke:browser -- --base-url http://127.0.0.1:3001`. Browser smoke artifacts stay local under `frontend/artifacts/` and are ignored from git.

Override the live target with `--base-url`, `--report-prefix`, or `--output-dir`.
