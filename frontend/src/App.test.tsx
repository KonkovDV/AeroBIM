import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ClashResult, DrawingAsset, ValidationIssue, ValidationReport } from "./lib/types";

const { fetchReportsMock, fetchReportMock } = vi.hoisted(() => ({
  fetchReportsMock: vi.fn(),
  fetchReportMock: vi.fn(),
}));

const clipboardWriteTextMock = vi.fn();
const createObjectURLMock = vi.fn();
const revokeObjectURLMock = vi.fn();

vi.mock("./lib/api", async () => {
  const actual = await vi.importActual<typeof import("./lib/api")>("./lib/api");
  return {
    ...actual,
    fetchReports: fetchReportsMock,
    fetchReport: fetchReportMock,
    getApiBaseUrl: () => "http://localhost:8080",
  };
});

vi.mock("./components/IfcViewerPanel", () => ({
  default: ({
    selectedGuids,
    selectionMode,
    selectionHeading,
    selectionDetail,
  }: {
    selectedGuids: string[];
    selectionMode: "none" | "issue" | "clash";
    selectionHeading: string;
    selectionDetail: string;
  }) => (
    <section data-testid="viewer-stub">
      <strong>{selectionHeading}</strong>
      <span>{selectionMode}</span>
      <p>{selectionDetail}</p>
      <div>{selectedGuids.join(",")}</div>
    </section>
  ),
}));

import App from "./App";
const REPORT_FILTERS_STORAGE_KEY = "aerobim-report-filters-v1";
const REPORT_FILTER_PRESETS_STORAGE_KEY = "aerobim-report-filter-presets-v1";

type MockReportSummary = {
  report_id: string;
  request_id: string;
  created_at: string;
  passed: boolean;
  issue_count: number;
  project_name?: string | null;
  discipline?: string | null;
};

function buildDrawingAsset(overrides: Partial<DrawingAsset>): DrawingAsset {
  return {
    asset_id: overrides.asset_id ?? "drawing-001-page-001",
    sheet_id: overrides.sheet_id ?? "A-101",
    page_number: overrides.page_number ?? 1,
    media_type: overrides.media_type ?? "image/png",
    coordinate_width: overrides.coordinate_width ?? 320,
    coordinate_height: overrides.coordinate_height ?? 200,
    stored_filename: overrides.stored_filename ?? "drawing-001-page-001.png",
  };
}

function buildIssue(overrides: Partial<ValidationIssue>): ValidationIssue {
  return {
    rule_id: overrides.rule_id ?? "DRAW-001",
    severity: overrides.severity ?? "error",
    message: overrides.message ?? "Drawing issue",
    ifc_entity: overrides.ifc_entity ?? "IFCWALL",
    category: overrides.category ?? "drawing-validation",
    target_ref: overrides.target_ref ?? "WALL-01",
    property_set: overrides.property_set ?? null,
    property_name: overrides.property_name ?? "thickness",
    operator: overrides.operator ?? "gte",
    expected_value: overrides.expected_value ?? "200",
    observed_value: overrides.observed_value ?? "150",
    unit: overrides.unit ?? "mm",
    element_guid: overrides.element_guid !== undefined ? overrides.element_guid : "guid-issue-1",
    problem_zone: overrides.problem_zone ?? {
      sheet_id: "A-102",
      page_number: 2,
      x: 10,
      y: 20,
      width: 100,
      height: 60,
      element_guid: null,
    },
    remark: overrides.remark ?? null,
  };
}

function buildClash(overrides: Partial<ClashResult>): ClashResult {
  return {
    element_a_guid: overrides.element_a_guid ?? "pipe-guid-a",
    element_b_guid: overrides.element_b_guid ?? "beam-guid-b",
    clash_type: overrides.clash_type ?? "hard",
    distance: overrides.distance ?? 0.03,
    description: overrides.description ?? "Hard clash between pipe and beam",
  };
}

function buildReport(): ValidationReport {
  return {
    report_id: "a".repeat(32),
    request_id: "req-001",
    ifc_path: "var/reports/model.ifc",
    created_at: "2026-04-13T09:00:00Z",
    project_name: "Residential Tower Alpha",
    discipline: "architecture",
    requirements: [],
    issues: [
      buildIssue({}),
      buildIssue({
        rule_id: "DRAW-SECOND",
        message: "Second drawing issue",
        target_ref: "SLAB-02",
        element_guid: null,
        problem_zone: {
          sheet_id: "A-101",
          page_number: 1,
          x: 30,
          y: 40,
          width: 80,
          height: 50,
          element_guid: null,
        },
      }),
    ],
    summary: {
      requirement_count: 0,
      issue_count: 2,
      error_count: 2,
      warning_count: 0,
      passed: false,
      drawing_annotation_count: 1,
      generated_remark_count: 0,
    },
    drawing_annotations: [],
    drawing_assets: [
      buildDrawingAsset({ asset_id: "asset-a101", sheet_id: "A-101", page_number: 1, stored_filename: "asset-a101.png" }),
      buildDrawingAsset({ asset_id: "asset-a102", sheet_id: "A-102", page_number: 2, stored_filename: "asset-a102.png" }),
    ],
    clash_results: [buildClash({})],
  };
}

function buildSecondReport(): ValidationReport {
  return {
    ...buildReport(),
    report_id: "b".repeat(32),
    request_id: "req-002",
    created_at: "2026-04-14T09:00:00Z",
    project_name: "Hospital Beta",
    discipline: "mechanical",
    summary: {
      requirement_count: 0,
      issue_count: 1,
      error_count: 0,
      warning_count: 1,
      passed: true,
      drawing_annotation_count: 1,
      generated_remark_count: 0,
    },
    issues: [
      buildIssue({
        rule_id: "DRAW-BETA-001",
        severity: "warning",
        message: "Hospital beta issue",
        target_ref: "MECH-01",
        element_guid: "guid-beta-1",
      }),
    ],
  };
}

function toReportSummary(report: ValidationReport): MockReportSummary {
  return {
    report_id: report.report_id,
    request_id: report.request_id,
    created_at: report.created_at,
    passed: report.summary.passed,
    issue_count: report.summary.issue_count,
    project_name: report.project_name,
    discipline: report.discipline,
  };
}

describe("App", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/");
    window.localStorage.clear();
    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: clipboardWriteTextMock,
      },
    });
    clipboardWriteTextMock.mockReset();
    clipboardWriteTextMock.mockResolvedValue(undefined);
    createObjectURLMock.mockReset();
    createObjectURLMock.mockReturnValue("blob:mock-preset-json");
    revokeObjectURLMock.mockReset();
    Object.defineProperty(window.URL, "createObjectURL", {
      configurable: true,
      value: createObjectURLMock,
    });
    Object.defineProperty(window.URL, "revokeObjectURL", {
      configurable: true,
      value: revokeObjectURLMock,
    });
    const report = buildReport();
    fetchReportsMock.mockReset();
    fetchReportMock.mockReset();
    fetchReportsMock.mockResolvedValue({
      reports: [toReportSummary(report)],
      count: 1,
    });
    fetchReportMock.mockResolvedValue(report);
  });

  it("loads the first report and focuses the viewer on the active issue guid", async () => {
    render(<App />);

    expect(await screen.findByRole("img", { name: /drawing evidence preview for a-102/i })).toBeTruthy();
    const viewer = await screen.findByTestId("viewer-stub");
    expect(within(viewer).getByText("DRAW-001")).toBeTruthy();
    expect(within(viewer).getByText("issue")).toBeTruthy();
    expect(within(viewer).getByText(/Single-element focus from the active issue GUID guid-issue-1/i)).toBeTruthy();
  });

  it("searches the loaded report set by report and request id", async () => {
    render(<App />);

    expect(await screen.findByText("Residential Tower Alpha")).toBeTruthy();
    fireEvent.change(screen.getByPlaceholderText("Search loaded reports"), { target: { value: "req-001" } });
    expect(await screen.findByText("Residential Tower Alpha")).toBeTruthy();

    fireEvent.change(screen.getByPlaceholderText("Search loaded reports"), { target: { value: "req-999" } });
    expect(await screen.findByText("No persisted reports match the current query.")).toBeTruthy();
  });

  it("forwards project, discipline, and status filters to the backend list API", async () => {
    const firstReport = buildReport();
    const secondReport = buildSecondReport();
    fetchReportsMock.mockImplementation(async (filters?: { project?: string; discipline?: string; passed?: boolean }) => {
      let reports = [firstReport, secondReport].map(toReportSummary);

      if (filters?.project) {
        reports = reports.filter((report) => (report.project_name ?? "").toLowerCase().includes(filters.project!.toLowerCase()));
      }
      if (filters?.discipline) {
        reports = reports.filter((report) => (report.discipline ?? "").toLowerCase().includes(filters.discipline!.toLowerCase()));
      }
      if (filters?.passed !== undefined) {
        reports = reports.filter((report) => report.passed === filters.passed);
      }

      return { reports, count: reports.length };
    });
    fetchReportMock.mockImplementation(async (reportId: string) => {
      return reportId === secondReport.report_id ? secondReport : firstReport;
    });

    render(<App />);

    expect(await screen.findByText("Residential Tower Alpha")).toBeTruthy();
    expect(screen.getByText("Hospital Beta")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Project filter"), { target: { value: "hospital" } });
    fireEvent.change(screen.getByLabelText("Discipline filter"), { target: { value: "mech" } });
    fireEvent.change(screen.getByLabelText("Status filter"), { target: { value: "passed" } });

    expect(await screen.findByText("Hospital Beta")).toBeTruthy();
    expect(screen.queryByText("Residential Tower Alpha")).toBeNull();
    expect(fetchReportsMock).toHaveBeenLastCalledWith({
      project: "hospital",
      discipline: "mech",
      passed: true,
    });
    expect(await screen.findByText("Hospital beta issue")).toBeTruthy();
  });

  it("groups report cards by project when grouping mode is enabled", async () => {
    const firstReport = buildReport();
    const secondReport = buildSecondReport();
    fetchReportsMock.mockResolvedValue({
      reports: [toReportSummary(firstReport), toReportSummary(secondReport)],
      count: 2,
    });
    fetchReportMock.mockImplementation(async (reportId: string) => {
      return reportId === secondReport.report_id ? secondReport : firstReport;
    });

    render(<App />);

    expect(await screen.findByText("Residential Tower Alpha")).toBeTruthy();
    expect(screen.getByText("Hospital Beta")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Group by project" }));

    expect(await screen.findByText("Residential Tower Alpha (1)")).toBeTruthy();
    expect(screen.getByText("Hospital Beta (1)")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Ungroup reports" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /bbbbbbbb/i }));
    expect(await screen.findByText("Hospital beta issue")).toBeTruthy();
  });

  it("loads persisted report filters from localStorage on startup", async () => {
    window.localStorage.setItem(
      REPORT_FILTERS_STORAGE_KEY,
      JSON.stringify({ project: "hospital", discipline: "mech", status: "passed" }),
    );
    fetchReportsMock.mockResolvedValue({ reports: [], count: 0 });

    render(<App />);

    expect(await screen.findByText("No persisted reports match the current query.")).toBeTruthy();
    expect(fetchReportsMock).toHaveBeenCalledWith({
      project: "hospital",
      discipline: "mech",
      passed: true,
    });
    expect((screen.getByLabelText("Project filter") as HTMLInputElement).value).toBe("hospital");
    expect((screen.getByLabelText("Discipline filter") as HTMLInputElement).value).toBe("mech");
    expect((screen.getByLabelText("Status filter") as HTMLSelectElement).value).toBe("passed");
  });

  it("prefers URL filters over localStorage and keeps URL in sync", async () => {
    window.localStorage.setItem(
      REPORT_FILTERS_STORAGE_KEY,
      JSON.stringify({ project: "residential", discipline: "architecture", status: "failed" }),
    );
    window.history.replaceState({}, "", "/?project=hospital&discipline=mech&status=passed");
    fetchReportsMock.mockResolvedValue({ reports: [], count: 0 });

    render(<App />);

    expect(await screen.findByText("No persisted reports match the current query.")).toBeTruthy();
    expect(fetchReportsMock).toHaveBeenCalledWith({
      project: "hospital",
      discipline: "mech",
      passed: true,
    });

    fireEvent.change(screen.getByLabelText("Project filter"), { target: { value: "tower" } });
    fireEvent.change(screen.getByLabelText("Discipline filter"), { target: { value: "arch" } });
    fireEvent.change(screen.getByLabelText("Status filter"), { target: { value: "failed" } });

    expect(window.location.search).toContain("project=tower");
    expect(window.location.search).toContain("discipline=arch");
    expect(window.location.search).toContain("status=failed");
  });

  it("copies the current filter state as a share link", async () => {
    render(<App />);

    expect(await screen.findByText("Residential Tower Alpha")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Project filter"), { target: { value: "hospital" } });
    fireEvent.change(screen.getByLabelText("Discipline filter"), { target: { value: "mech" } });
    fireEvent.change(screen.getByLabelText("Status filter"), { target: { value: "passed" } });

    fireEvent.click(screen.getByRole("button", { name: "Copy share link" }));

    expect(await screen.findByText("Link copied")).toBeTruthy();
    expect(clipboardWriteTextMock).toHaveBeenCalledTimes(1);
    const copiedLink = String(clipboardWriteTextMock.mock.calls[0][0]);
    expect(copiedLink).toContain("project=hospital");
    expect(copiedLink).toContain("discipline=mech");
    expect(copiedLink).toContain("status=passed");
  });

  it("loads, applies, saves, and removes filter presets", async () => {
    window.localStorage.setItem(
      REPORT_FILTER_PRESETS_STORAGE_KEY,
      JSON.stringify([
        {
          id: "preset-1",
          name: "Hospital Passed",
          filters: { project: "hospital", discipline: "mech", status: "passed" },
        },
      ]),
    );

    render(<App />);

    expect(await screen.findByRole("button", { name: "Hospital Passed" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Hospital Passed" }));

    expect((screen.getByLabelText("Project filter") as HTMLInputElement).value).toBe("hospital");
    expect((screen.getByLabelText("Discipline filter") as HTMLInputElement).value).toBe("mech");
    expect((screen.getByLabelText("Status filter") as HTMLSelectElement).value).toBe("passed");

    fireEvent.change(screen.getByLabelText("Preset name"), { target: { value: "Tower Failed" } });
    fireEvent.change(screen.getByLabelText("Preset scope"), { target: { value: "team" } });
    fireEvent.change(screen.getByLabelText("Project filter"), { target: { value: "tower" } });
    fireEvent.change(screen.getByLabelText("Discipline filter"), { target: { value: "arch" } });
    fireEvent.change(screen.getByLabelText("Status filter"), { target: { value: "failed" } });
    fireEvent.click(screen.getByRole("button", { name: "Save preset" }));

    expect(screen.getByRole("button", { name: "Tower Failed" })).toBeTruthy();
    expect(screen.getByText("team")).toBeTruthy();
    const savedPresetsRaw = window.localStorage.getItem(REPORT_FILTER_PRESETS_STORAGE_KEY);
    expect(savedPresetsRaw).not.toBeNull();
    const savedPresets = JSON.parse(savedPresetsRaw ?? "[]") as Array<{ name: string; scope?: string }>;
    expect(savedPresets.some((preset) => preset.name === "Tower Failed")).toBe(true);
    expect(savedPresets.some((preset) => preset.name === "Tower Failed" && preset.scope === "team")).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "Remove preset Tower Failed" }));
    expect(screen.queryByRole("button", { name: "Tower Failed" })).toBeNull();
  });

  it("exports and imports presets as JSON payload", async () => {
    window.localStorage.setItem(
      REPORT_FILTER_PRESETS_STORAGE_KEY,
      JSON.stringify([
        {
          id: "preset-1",
          name: "Hospital Passed",
          filters: { project: "hospital", discipline: "mech", status: "passed" },
        },
      ]),
    );

    render(<App />);

    expect(await screen.findByRole("button", { name: "Hospital Passed" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Copy presets JSON" }));

    expect(await screen.findByText("Preset JSON copied")).toBeTruthy();
    expect(clipboardWriteTextMock).toHaveBeenCalledTimes(1);
    const exportedPayload = String(clipboardWriteTextMock.mock.calls[0][0]);
    expect(exportedPayload).toContain("Hospital Passed");

    fireEvent.change(screen.getByLabelText("Preset import payload"), {
      target: {
        value: JSON.stringify([
          {
            name: "Tower Failed",
            filters: {
              project: "tower",
              discipline: "arch",
              status: "failed",
            },
          },
        ]),
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Import presets JSON" }));

    expect(await screen.findByText("Preset JSON imported")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Tower Failed" })).toBeTruthy();
    expect(screen.getByText("team")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Tower Failed" }));
    expect((screen.getByLabelText("Project filter") as HTMLInputElement).value).toBe("tower");
    expect((screen.getByLabelText("Discipline filter") as HTMLInputElement).value).toBe("arch");
    expect((screen.getByLabelText("Status filter") as HTMLSelectElement).value).toBe("failed");
  });

  it("downloads and imports presets through JSON file flow", async () => {
    window.localStorage.setItem(
      REPORT_FILTER_PRESETS_STORAGE_KEY,
      JSON.stringify([
        {
          id: "preset-1",
          name: "Hospital Passed",
          filters: { project: "hospital", discipline: "mech", status: "passed" },
        },
      ]),
    );

    render(<App />);

    expect(await screen.findByRole("button", { name: "Hospital Passed" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Download presets JSON" }));

    expect(await screen.findByText("Preset JSON downloaded")).toBeTruthy();
    expect(createObjectURLMock).toHaveBeenCalledTimes(1);
    expect(revokeObjectURLMock).toHaveBeenCalledTimes(1);

    const upload = screen.getByLabelText("Import presets file") as HTMLInputElement;
    const file = new File(
      [
        JSON.stringify([
          {
            name: "Campus Passed",
            filters: { project: "campus", discipline: "structure", status: "passed" },
          },
        ]),
      ],
      "presets.json",
      { type: "application/json" },
    );
    fireEvent.change(upload, { target: { files: [file] } });

    expect(await screen.findByText("Preset JSON imported")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Campus Passed" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Campus Passed" }));
    expect((screen.getByLabelText("Project filter") as HTMLInputElement).value).toBe("campus");
    expect((screen.getByLabelText("Discipline filter") as HTMLInputElement).value).toBe("structure");
    expect((screen.getByLabelText("Status filter") as HTMLSelectElement).value).toBe("passed");
  });

  it("covers the review-shell smoke path across export, provenance, 2d overlay, and clash focus", async () => {
    const { container } = render(<App />);

    const firstImage = await screen.findByRole("img", { name: /drawing evidence preview for a-102/i });
    Object.defineProperty(firstImage, "naturalWidth", { configurable: true, value: 640 });
    Object.defineProperty(firstImage, "naturalHeight", { configurable: true, value: 400 });
    fireEvent.load(firstImage);

    const htmlLink = screen.getByRole("link", { name: "HTML" }) as HTMLAnchorElement;
    const jsonLink = screen.getByRole("link", { name: "JSON" }) as HTMLAnchorElement;
    const bcfLink = screen.getByRole("link", { name: "BCF" }) as HTMLAnchorElement;

    expect(htmlLink.href).toContain("/v1/reports/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/export/html");
    expect(jsonLink.href).toContain("/v1/reports/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/export/json");
    expect(bcfLink.href).toContain("/v1/reports/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/export/bcf");
    const drawingEvidencePanel = container.querySelector(".drawing-evidence-panel") as HTMLElement;
    const activeIssueBlock = screen.getByText("Active issue").closest(".detail-block") as HTMLElement;
    expect(within(drawingEvidencePanel).getAllByText("A-102 · page 2").length).toBeGreaterThanOrEqual(2);
    await waitFor(() => {
      expect(container.querySelector(".drawing-evidence-rect")).toBeTruthy();
    });
    expect(within(activeIssueBlock).getByText("WALL-01")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /DRAW-SECOND/i }));
    const secondImage = await screen.findByRole("img", { name: /drawing evidence preview for a-101/i });
    Object.defineProperty(secondImage, "naturalWidth", { configurable: true, value: 640 });
    Object.defineProperty(secondImage, "naturalHeight", { configurable: true, value: 400 });
    fireEvent.load(secondImage);

    const viewerAfterIssueSwitch = await screen.findByTestId("viewer-stub");
    const activeIssueBlockAfterSwitch = screen.getByText("Active issue").closest(".detail-block") as HTMLElement;
    expect(within(viewerAfterIssueSwitch).getByText("No spatial selection")).toBeTruthy();
    expect(within(activeIssueBlockAfterSwitch).getByText("SLAB-02")).toBeTruthy();
    expect(container.querySelector(".drawing-evidence-rect")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Hard clash between pipe and beam/i }));

    const viewerAfterClashSwitch = await screen.findByTestId("viewer-stub");
    expect(within(viewerAfterClashSwitch).getByText(/hard clash pair/i)).toBeTruthy();
    expect(within(viewerAfterClashSwitch).getByText(/pipe-guid-a,beam-guid-b/i)).toBeTruthy();
  });

  it("switches the 2d evidence panel when another issue is selected", async () => {
    render(<App />);

    await screen.findByRole("img", { name: /drawing evidence preview for a-102/i });
    fireEvent.click(screen.getByRole("button", { name: /DRAW-SECOND/i }));

    expect(await screen.findByRole("img", { name: /drawing evidence preview for a-101/i })).toBeTruthy();
    expect(screen.getByText(/plain drawing-preview mode|Preview loaded, but the current issue/i)).toBeTruthy();
    const viewer = await screen.findByTestId("viewer-stub");
    expect(await within(viewer).findByText("No spatial selection")).toBeTruthy();
  });

  it("switches the viewer focus to a clash pair when a clash card is selected", async () => {
    render(<App />);

    await screen.findByRole("img", { name: /drawing evidence preview for a-102/i });
    fireEvent.click(screen.getByRole("button", { name: /Hard clash between pipe and beam/i }));

    const viewer = await screen.findByTestId("viewer-stub");
    expect(await within(viewer).findByText(/hard clash pair/i)).toBeTruthy();
    expect(within(viewer).getByText("clash")).toBeTruthy();
    expect(within(viewer).getByText(/pipe-guid-a,beam-guid-b/i)).toBeTruthy();
  });
});