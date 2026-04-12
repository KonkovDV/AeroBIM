# Frontend Source Tree

Active runtime source for the AeroBIM review shell.

Top-level files:

- `App.tsx` — application shell and interaction flow;
- `components/IfcViewerPanel.tsx` — lazy-loaded spatial review panel;
- `styles.css` — visual system and responsive layout;
- `lib/api.ts` — browser-side report API client;
- `lib/ifc-scene.ts` — raw `web-ifc + Three.js` scene controller;
- `lib/types.ts` — shared browser response types.