# AeroBIM Smoke Path

## Goal

Provide a narrow-first runtime check for the standalone stack.

Note: the frontend repo now has App-level automated regression coverage for the same review-shell chain. The steps below remain the runtime verification path against a live persisted backend report.

## One-Command Live Smoke

For the smallest fully automated local runtime proof, run:

```bash
cd backend
python -m aerobim.tools.run_live_review_smoke
```

The command boots an isolated backend/frontend pair, seeds the deterministic report, captures browser artifacts, and prints a JSON payload with the seeded report and screenshot/trace paths.

Inside the parent VS Code workspace, the same rail is now available as the `process: smoke:live-review` task.

## Local Backend Smoke

1. Start the backend.
2. Verify health:

```bash
curl http://127.0.0.1:8080/health
```

3. Seed one deterministic persisted smoke report:

```bash
cd backend
python -m aerobim.tools.seed_smoke_report
```

4. Verify empty or existing report index:

```bash
curl http://127.0.0.1:8080/v1/reports
```

5. Re-check `GET /v1/reports` and confirm the seeded report appears.
6. Open the seeded report and verify source + preview + export endpoints:

```bash
curl http://127.0.0.1:8080/v1/reports/<report_id>
curl -I http://127.0.0.1:8080/v1/reports/<report_id>/source/ifc
curl -I http://127.0.0.1:8080/v1/reports/<report_id>/drawing-assets/<asset_id>/preview
curl -I http://127.0.0.1:8080/v1/reports/<report_id>/export/html
curl -I http://127.0.0.1:8080/v1/reports/<report_id>/export/bcf
```

## Frontend Smoke

1. Start the frontend dev server.
2. Open `http://127.0.0.1:5173`.
3. Confirm the shell renders the seeded smoke report in the list.
4. Select a report and confirm issue detail plus provenance panes populate.
5. Confirm the IFC viewer loads the report-scoped model.
6. Select an issue with `element_guid` and confirm the viewer highlights it.
7. Select a clash card and confirm the viewer highlights both clash elements.
8. Select an issue with `problem_zone` evidence and confirm the 2D drawing overlay panel loads a persisted preview asset.
9. Confirm the overlay rectangle lands on the rendered sheet/page region rather than on an empty panel.
10. Switch the 2D panel to another persisted drawing asset and confirm the panel stays usable in browse mode even when the issue overlay is hidden.
11. Toggle isolate mode and confirm only the selected issue element or clash pair remains visible.
12. Trigger HTML, JSON, and BCF downloads.
13. Capture browser-level smoke artifacts:

```bash
cd frontend
npm run smoke:browser
```

## Docker Smoke

1. Start the backend stack with the compose file.
2. Wait for the backend healthcheck to turn healthy.
3. Verify the same `/health` and `/v1/reports` endpoints from the host.
4. Confirm new report JSON files appear under the bound report volume.

## Regression Gate

The smoke path is complete only when:

- backend health is green;
- report listing works;
- at least one report detail resolves;
- the report-scoped IFC source endpoint responds successfully;
- the report-scoped drawing preview endpoint responds successfully for one persisted asset;
- the deterministic smoke seeder can recreate the same live report payload on demand;
- the frontend viewer loads one model and reacts to both issue and clash-pair selection;
- the frontend 2D panel renders one persisted issue overlay on drawing evidence;
- the browser smoke harness emits at least one full-page screenshot plus one Playwright trace zip against the seeded live stack;
- all three export endpoints respond successfully;
- frontend renders list + issue + provenance for the same report.