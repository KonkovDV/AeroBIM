import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ClashResult, DrawingAsset, ValidationIssue, ValidationReport } from "./lib/types";

const { fetchReportsMock, fetchReportMock } = vi.hoisted(() => ({
  fetchReportsMock: vi.fn(),
  fetchReportMock: vi.fn(),
}));

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
    expect(container.querySelector(".drawing-evidence-rect")).toBeTruthy();
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