# Frontend Boundary

The frontend is a separate bounded context.

Its job is not to own validation semantics. Its job is to:

- load model and report data;
- load drawing pages and 2D problem zones;
- present findings and rule provenance;
- navigate from issue to model object;
- render bounding boxes or overlay hints for 2D evidence;
- export or forward issues to external workflows.

## Planned Stack

- React + TypeScript
- Vite
- `web-ifc` as default browser IFC engine
- optional APS Viewer adapter for enterprise mixed-format deployments

## First UI Milestones

1. report list
2. issue detail panel
3. element highlight / isolate workflow
4. PDF/image layer with 2D bounding-box overlays
5. requirement-to-finding navigation
6. export actions
