import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ClashResult, DrawingAsset, ValidationIssue, ValidationReport } from "./lib/types";

const {
  fetchReportsMock,
  fetchReportMock,
  postReviewEventMock,
  fetchReviewEventsMock,
  uploadDocumentMock,
  submitAnalyzeProjectPackageMock,
  fetchAuthBffMock,
  fetchAuthSessionMock,
  seedDemoFixtureMock,
} = vi.hoisted(() => ({
  fetchReportsMock: vi.fn(),
  fetchReportMock: vi.fn(),
  postReviewEventMock: vi.fn(),
  fetchReviewEventsMock: vi.fn(),
  uploadDocumentMock: vi.fn(),
  submitAnalyzeProjectPackageMock: vi.fn(),
  fetchAuthBffMock: vi.fn(),
  fetchAuthSessionMock: vi.fn(),
  seedDemoFixtureMock: vi.fn(),
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
    postReviewEvent: postReviewEventMock,
    fetchReviewEvents: fetchReviewEventsMock,
    uploadDocument: uploadDocumentMock,
    submitAnalyzeProjectPackage: submitAnalyzeProjectPackageMock,
    fetchAuthBff: fetchAuthBffMock,
    fetchAuthSession: fetchAuthSessionMock,
    seedDemoFixture: seedDemoFixtureMock,
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
import { UI_COPY } from "./lib/ui-copy";
const REPORT_FILTERS_STORAGE_KEY = "aerobim-report-filters-v1";
const REPORT_FILTER_PRESETS_STORAGE_KEY = "aerobim-report-filter-presets-v1";

function openProjectsIndex(): void {
  fireEvent.click(screen.getByRole("button", { name: "Проекты" }));
}

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
    finding_id: overrides.finding_id ?? "fid-draw-001",
    source_id: overrides.source_id ?? "drawing:A-102",
    evidence_refs: overrides.evidence_refs ?? ["drawing:A-102#sheet:A-102"],
    evidence_modality: overrides.evidence_modality ?? "drawing",
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
      outcome: "blocked",
    },
    drawing_annotations: [],
    drawing_assets: [
      buildDrawingAsset({ asset_id: "asset-openrebar", sheet_id: "A-101", page_number: 1, stored_filename: "asset-openrebar.png" }),
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
    fetchAuthBffMock.mockReset();
    fetchAuthBffMock.mockResolvedValue({ httpStatus: 501, status: "NOT_IMPLEMENTED" });
    fetchAuthSessionMock.mockReset();
    fetchAuthSessionMock.mockResolvedValue(null);
    postReviewEventMock.mockReset();
    postReviewEventMock.mockImplementation(async (_reportId: string, body: { event_type: string; issue_rule_id?: string; finding_id?: string; previous_state?: string }) => {
      const resulting =
        body.event_type === "edited_remark"
          ? "edited"
          : body.event_type === "triaged"
            ? "opened"
            : body.event_type;
      return {
        event: {
          event_id: `${body.event_type}-${body.issue_rule_id ?? "none"}-${resulting}`,
          event_type: body.event_type,
          created_at: "2026-09-03T00:00:00Z",
          issue_rule_id: body.issue_rule_id ?? null,
          finding_id: body.finding_id ?? null,
          resulting_state: resulting,
          previous_state: body.previous_state ?? null,
        },
      };
    });
    fetchReviewEventsMock.mockReset();
    fetchReviewEventsMock.mockResolvedValue({ events: [], count: 0 });
    uploadDocumentMock.mockReset();
    submitAnalyzeProjectPackageMock.mockReset();
    seedDemoFixtureMock.mockReset();
    fetchReportsMock.mockResolvedValue({
      reports: [toReportSummary(report)],
      count: 1,
    });
    fetchReportMock.mockResolvedValue(report);
  });

  it("loads the first report and focuses the viewer on the active issue guid", async () => {
    render(<App />);

    expect(await screen.findByRole("img", { name: /Превью чертежа a-102/i })).toBeTruthy();
    expect(screen.getByTestId("role-honesty-banner").textContent).toMatch(/не разграничение доступа/);
    expect(screen.getByTestId("training-rules-banner").textContent).toMatch(/учебном наборе правил/);
    expect(screen.getAllByText(/BLOCKED/).length).toBeGreaterThan(0);
    const viewer = await screen.findByTestId("viewer-stub");
    expect(within(viewer).getByText("DRAW-001")).toBeTruthy();
    expect(within(viewer).getByText("issue")).toBeTruthy();
    expect(within(viewer).getByText(/Фокус на одном элементе по GUID guid-issue-1/i)).toBeTruthy();
  });

  it("snaps the selected finding to the first visible row when search hides it", async () => {
    render(<App />);
    expect(await screen.findByLabelText(UI_COPY.searchFindings)).toBeTruthy();
    fireEvent.change(screen.getByLabelText(UI_COPY.searchFindings), { target: { value: "Second" } });
    await waitFor(() => {
      expect(screen.queryByText("Drawing issue")).toBeNull();
    });
    const cards = screen
      .getAllByRole("button")
      .filter((button) => button.className.includes("issue-card"));
    expect(cards).toHaveLength(1);
    expect(cards[0]?.className).toMatch(/active/);
    expect(cards[0]?.textContent).toMatch(/DRAW-SECOND/);
  });

  it("retries the report list after a failed fetch", async () => {
    fetchReportsMock.mockRejectedValueOnce(new Error("API down"));
    fetchReportsMock.mockResolvedValue({
      reports: [toReportSummary(buildReport())],
      count: 1,
    });
    render(<App />);
    expect(await screen.findByTestId("error-banner")).toBeTruthy();
    expect(screen.getByTestId("error-banner").textContent).toMatch(/API down/);
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.retry }));
    expect(await screen.findByLabelText(UI_COPY.searchFindings)).toBeTruthy();
  });

  it("offers projects and upload from an empty expert pane", async () => {
    fetchReportsMock.mockResolvedValue({ reports: [], count: 0 });
    render(<App />);
    expect(await screen.findByRole("button", { name: UI_COPY.openProjects })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.openProjects }));
    expect(await screen.findByTestId("projects-index")).toBeTruthy();
  });

  it("searches the loaded report set by report and request id", async () => {
    render(<App />);

    expect(await screen.findByText("Residential Tower Alpha")).toBeTruthy();
    openProjectsIndex();
    fireEvent.change(screen.getByPlaceholderText(UI_COPY.searchReports), { target: { value: "req-001" } });
    expect(await screen.findByText("Residential Tower Alpha")).toBeTruthy();

    fireEvent.change(screen.getByPlaceholderText(UI_COPY.searchReports), { target: { value: "req-999" } });
    expect(await screen.findByText("Нет сохранённых отчётов по текущему запросу.")).toBeTruthy();
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
    openProjectsIndex();
    expect(screen.getByText("Hospital Beta")).toBeTruthy();

    fireEvent.change(screen.getByLabelText(UI_COPY.filterProject), { target: { value: "hospital" } });
    fireEvent.change(screen.getByLabelText(UI_COPY.filterDiscipline), { target: { value: "mech" } });
    fireEvent.change(screen.getByLabelText(UI_COPY.filterStatus), { target: { value: "passed" } });

    expect(await screen.findByText("Hospital Beta")).toBeTruthy();
    expect(screen.queryByText("Residential Tower Alpha")).toBeNull();
    expect(fetchReportsMock).toHaveBeenLastCalledWith(
      {
        project: "hospital",
        discipline: "mech",
        passed: true,
      },
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
    fireEvent.click(screen.getByRole("button", { name: /bbbbbbbb/i }));
    expect((await screen.findAllByText("Hospital beta issue")).length).toBeGreaterThan(0);
  });

  it("ignores a stale reports list after filters change", async () => {
    const firstReport = buildReport();
    const secondReport = buildSecondReport();
    let releaseStale: (value: { reports: MockReportSummary[]; count: number }) => void = () => {
      throw new Error("stale reports gate was not armed");
    };
    const staleGate = new Promise<{ reports: MockReportSummary[]; count: number }>((resolve) => {
      releaseStale = resolve;
    });

    fetchReportsMock.mockImplementationOnce(async () => staleGate);
    fetchReportsMock.mockResolvedValue({
      reports: [toReportSummary(secondReport)],
      count: 1,
    });
    fetchReportMock.mockImplementation(async (reportId: string) => {
      return reportId === secondReport.report_id ? secondReport : firstReport;
    });

    render(<App />);
    openProjectsIndex();
    fireEvent.change(screen.getByLabelText(UI_COPY.filterProject), { target: { value: "hospital" } });

    await waitFor(() => {
      expect(fetchReportsMock.mock.calls.length).toBeGreaterThanOrEqual(2);
    });

    releaseStale({ reports: [toReportSummary(firstReport)], count: 1 });

    expect(await screen.findByText("Hospital Beta")).toBeTruthy();
    expect(screen.queryByText("Residential Tower Alpha")).toBeNull();
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
    openProjectsIndex();
    expect(screen.getByText("Hospital Beta")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: UI_COPY.groupByProject }));

    expect(await screen.findByText("Residential Tower Alpha (1)")).toBeTruthy();
    expect(screen.getByText("Hospital Beta (1)")).toBeTruthy();
    expect(screen.getByRole("button", { name: UI_COPY.ungroupReports })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /bbbbbbbb/i }));
    expect((await screen.findAllByText("Hospital beta issue")).length).toBeGreaterThan(0);
  });

  it("loads persisted report filters from localStorage on startup", async () => {
    window.localStorage.setItem(
      REPORT_FILTERS_STORAGE_KEY,
      JSON.stringify({ project: "hospital", discipline: "mech", status: "passed" }),
    );
    fetchReportsMock.mockResolvedValue({ reports: [], count: 0 });

    render(<App />);

    openProjectsIndex();
    expect(await screen.findByText("Нет сохранённых отчётов по текущему запросу.")).toBeTruthy();
    expect(fetchReportsMock).toHaveBeenCalledWith(
      {
        project: "hospital",
        discipline: "mech",
        passed: true,
      },
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
    expect((screen.getByLabelText(UI_COPY.filterProject) as HTMLInputElement).value).toBe("hospital");
    expect((screen.getByLabelText(UI_COPY.filterDiscipline) as HTMLInputElement).value).toBe("mech");
    expect((screen.getByLabelText(UI_COPY.filterStatus) as HTMLSelectElement).value).toBe("passed");
  });

  it("prefers URL filters over localStorage and keeps URL in sync", async () => {
    window.localStorage.setItem(
      REPORT_FILTERS_STORAGE_KEY,
      JSON.stringify({ project: "residential", discipline: "architecture", status: "failed" }),
    );
    window.history.replaceState({}, "", "/?project=hospital&discipline=mech&status=passed");
    fetchReportsMock.mockResolvedValue({ reports: [], count: 0 });

    render(<App />);

    openProjectsIndex();
    expect(await screen.findByText("Нет сохранённых отчётов по текущему запросу.")).toBeTruthy();
    expect(fetchReportsMock).toHaveBeenCalledWith(
      {
        project: "hospital",
        discipline: "mech",
        passed: true,
      },
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );

    fireEvent.change(screen.getByLabelText(UI_COPY.filterProject), { target: { value: "tower" } });
    fireEvent.change(screen.getByLabelText(UI_COPY.filterDiscipline), { target: { value: "arch" } });
    fireEvent.change(screen.getByLabelText(UI_COPY.filterStatus), { target: { value: "failed" } });

    expect(window.location.search).toContain("project=tower");
    expect(window.location.search).toContain("discipline=arch");
    expect(window.location.search).toContain("status=failed");
  });

  it("copies the current filter state as a share link", async () => {
    render(<App />);

    expect(await screen.findByText("Residential Tower Alpha")).toBeTruthy();
    openProjectsIndex();
    fireEvent.change(screen.getByLabelText(UI_COPY.filterProject), { target: { value: "hospital" } });
    fireEvent.change(screen.getByLabelText(UI_COPY.filterDiscipline), { target: { value: "mech" } });
    fireEvent.change(screen.getByLabelText(UI_COPY.filterStatus), { target: { value: "passed" } });

    fireEvent.click(screen.getByRole("button", { name: UI_COPY.copyShareLink }));

    expect(await screen.findByText(UI_COPY.linkCopied)).toBeTruthy();
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

    openProjectsIndex();
    expect(await screen.findByRole("button", { name: "Hospital Passed" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Hospital Passed" }));

    expect((screen.getByLabelText(UI_COPY.filterProject) as HTMLInputElement).value).toBe("hospital");
    expect((screen.getByLabelText(UI_COPY.filterDiscipline) as HTMLInputElement).value).toBe("mech");
    expect((screen.getByLabelText(UI_COPY.filterStatus) as HTMLSelectElement).value).toBe("passed");

    fireEvent.change(screen.getByLabelText("Имя пресета"), { target: { value: "Tower Failed" } });
    fireEvent.change(screen.getByLabelText("Область пресета"), { target: { value: "file" } });
    fireEvent.change(screen.getByLabelText(UI_COPY.filterProject), { target: { value: "tower" } });
    fireEvent.change(screen.getByLabelText(UI_COPY.filterDiscipline), { target: { value: "arch" } });
    fireEvent.change(screen.getByLabelText(UI_COPY.filterStatus), { target: { value: "failed" } });
    fireEvent.click(screen.getByRole("button", { name: "Сохранить пресет" }));

    expect(screen.getByRole("button", { name: "Tower Failed" })).toBeTruthy();
    expect(screen.getAllByText("Обмен через JSON").length).toBeGreaterThan(0);
    const savedPresetsRaw = window.localStorage.getItem(REPORT_FILTER_PRESETS_STORAGE_KEY);
    expect(savedPresetsRaw).not.toBeNull();
    const savedPresets = JSON.parse(savedPresetsRaw ?? "[]") as Array<{ name: string; scope?: string }>;
    expect(savedPresets.some((preset) => preset.name === "Tower Failed")).toBe(true);
    expect(savedPresets.some((preset) => preset.name === "Tower Failed" && preset.scope === "file")).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: UI_COPY.removePreset("Tower Failed") }));
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

    openProjectsIndex();
    expect(await screen.findByRole("button", { name: "Hospital Passed" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.copyPresets }));

    expect(await screen.findByText(UI_COPY.presetCopied)).toBeTruthy();
    expect(clipboardWriteTextMock).toHaveBeenCalledTimes(1);
    const exportedPayload = String(clipboardWriteTextMock.mock.calls[0][0]);
    expect(exportedPayload).toContain("Hospital Passed");

    fireEvent.change(screen.getByLabelText(UI_COPY.presetImportPayload), {
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
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.importPresetsJson }));

    expect(await screen.findByText(UI_COPY.presetImported)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Tower Failed" })).toBeTruthy();
    expect(screen.getAllByText("Этот браузер").length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Tower Failed" }));
    expect((screen.getByLabelText(UI_COPY.filterProject) as HTMLInputElement).value).toBe("tower");
    expect((screen.getByLabelText(UI_COPY.filterDiscipline) as HTMLInputElement).value).toBe("arch");
    expect((screen.getByLabelText(UI_COPY.filterStatus) as HTMLSelectElement).value).toBe("failed");
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

    openProjectsIndex();
    expect(await screen.findByRole("button", { name: "Hospital Passed" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.downloadPresets }));

    expect(await screen.findByText(UI_COPY.presetDownloaded)).toBeTruthy();
    expect(createObjectURLMock).toHaveBeenCalledTimes(1);
    expect(revokeObjectURLMock).toHaveBeenCalledTimes(1);

    const upload = screen.getByLabelText(UI_COPY.importPresetsFile) as HTMLInputElement;
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

    expect(await screen.findByText(UI_COPY.presetImported)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Campus Passed" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Campus Passed" }));
    expect((screen.getByLabelText(UI_COPY.filterProject) as HTMLInputElement).value).toBe("campus");
    expect((screen.getByLabelText(UI_COPY.filterDiscipline) as HTMLInputElement).value).toBe("structure");
    expect((screen.getByLabelText(UI_COPY.filterStatus) as HTMLSelectElement).value).toBe("passed");
  });

  it("covers the review-shell smoke path across export, provenance, 2d overlay, and clash focus", async () => {
    const { container } = render(<App />);

    const firstImage = await screen.findByRole("img", { name: /Превью чертежа a-102/i });
    Object.defineProperty(firstImage, "naturalWidth", { configurable: true, value: 640 });
    Object.defineProperty(firstImage, "naturalHeight", { configurable: true, value: 400 });
    fireEvent.load(firstImage);

    expect(screen.getByRole("button", { name: "HTML" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "JSON" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "BCF" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "BCF 3.0" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "PDF (черновик покрытия)" })).toBeTruthy();
    const drawingEvidencePanel = container.querySelector(".drawing-evidence-panel") as HTMLElement;
    const activeIssueBlock = screen.getByTestId("provenance-active-issue");
    expect(within(drawingEvidencePanel).getAllByText("A-102 · стр. 2").length).toBeGreaterThanOrEqual(2);
    await waitFor(() => {
      expect(container.querySelector(".drawing-evidence-rect")).toBeTruthy();
    });
    expect(within(activeIssueBlock).getByText("WALL-01")).toBeTruthy();
    expect(within(activeIssueBlock).getByText(UI_COPY.provenanceOk)).toBeTruthy();
    expect(within(activeIssueBlock).getByText("fid-draw-001")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /DRAW-SECOND/i }));
    const secondImage = await screen.findByRole("img", { name: /Превью чертежа a-101/i });
    Object.defineProperty(secondImage, "naturalWidth", { configurable: true, value: 640 });
    Object.defineProperty(secondImage, "naturalHeight", { configurable: true, value: 400 });
    fireEvent.load(secondImage);

    const viewerAfterIssueSwitch = await screen.findByTestId("viewer-stub");
    const activeIssueBlockAfterSwitch = screen.getByTestId("provenance-active-issue");
    expect(within(viewerAfterIssueSwitch).getByText(UI_COPY.spatialNone)).toBeTruthy();
    expect(within(activeIssueBlockAfterSwitch).getByText("SLAB-02")).toBeTruthy();
    expect(container.querySelector(".drawing-evidence-rect")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Hard clash between pipe and beam/i }));

    const viewerAfterClashSwitch = await screen.findByTestId("viewer-stub");
    expect(within(viewerAfterClashSwitch).getByText(/пара клэша/)).toBeTruthy();
    expect(within(viewerAfterClashSwitch).getByText(/pipe-guid-a,beam-guid-b/i)).toBeTruthy();
  });

  it("switches the 2d evidence panel when another issue is selected", async () => {
    render(<App />);

    await screen.findByRole("img", { name: /Превью чертежа a-102/i });
    fireEvent.click(screen.getByRole("button", { name: /DRAW-SECOND/i }));

    expect(await screen.findByRole("img", { name: /Превью чертежа a-101/i })).toBeTruthy();
    expect(screen.getAllByText("DRAW-SECOND").length).toBeGreaterThan(0);
    const viewer = await screen.findByTestId("viewer-stub");
    expect(await within(viewer).findByText(UI_COPY.spatialNone)).toBeTruthy();
  });

  it("switches the viewer focus to a clash pair when a clash card is selected", async () => {
    render(<App />);

    await screen.findByRole("img", { name: /Превью чертежа a-102/i });
    fireEvent.click(screen.getByRole("button", { name: /Hard clash between pipe and beam/i }));

    const viewer = await screen.findByTestId("viewer-stub");
    expect(await within(viewer).findByText(/пара клэша/)).toBeTruthy();
    expect(within(viewer).getByText("clash")).toBeTruthy();
    expect(within(viewer).getByText(/pipe-guid-a,beam-guid-b/i)).toBeTruthy();
  });

  it("renders clash triage band chips and orders issues by priority", async () => {
    const report = buildReport();
    report.issues = [
      {
        ...buildIssue({
          rule_id: "SPATIAL-NEGLIGIBLE",
          severity: "warning",
          message: "tiny clash",
          category: "spatial",
          evidence_refs: ["n1", "n2", "triage:band=negligible", "triage:rank=2"],
        }),
        priority: 30,
      },
      {
        ...buildIssue({
          rule_id: "SPATIAL-CRITICAL",
          severity: "warning",
          message: "deep clash",
          category: "spatial",
          evidence_refs: ["c1", "c2", "triage:band=critical", "triage:rank=1"],
        }),
        priority: 42,
      },
    ];
    fetchReportMock.mockResolvedValue(report);

    render(<App />);

    const criticalChip = await screen.findByText("критично", { selector: ".triage-band" });
    expect(criticalChip.className).toContain("triage-band-critical");
    const negligibleChip = screen.getByText("незначительная", { selector: ".triage-band" });
    expect(negligibleChip.className).toContain("triage-band-negligible");

    // Priority-desc reviewer order: critical card must precede negligible card.
    const cards = screen.getAllByRole("button", { name: /SPATIAL-/i });
    expect(cards[0].textContent).toContain("SPATIAL-CRITICAL");
    expect(cards[1].textContent).toContain("SPATIAL-NEGLIGIBLE");
  });

  it("marks advisory-origin issues as candidates, distinct from confirmed deterministic findings", async () => {
    const report = buildReport();
    report.issues = [
      { ...buildIssue({ rule_id: "ADV-CAND-001", severity: "error", message: "model region reading" }), origin: "advisory" },
      { ...buildIssue({ rule_id: "DET-CONF-001", severity: "error", message: "engine confirmed finding" }), origin: "deterministic" },
    ];
    fetchReportMock.mockResolvedValue(report);

    render(<App />);

    const advisoryCard = await screen.findByRole("button", { name: /ADV-CAND-001/i });
    const deterministicCard = screen.getByRole("button", { name: /DET-CONF-001/i });

    // Advisory observation is visually marked as a candidate needing review — §12:
    // it must not read as a confirmed verdict/error.
    expect(advisoryCard.className).toContain("issue-card--advisory");
    expect(within(advisoryCard).getByText(UI_COPY.advisory)).toBeTruthy();
    expect(within(advisoryCard).getByTitle(/не подтверждённый вердикт/i)).toBeTruthy();

    // A deterministic finding carries no advisory-candidate cue.
    expect(deterministicCard.className).not.toContain("issue-card--advisory");
    expect(within(deterministicCard).queryByText(UI_COPY.advisory)).toBeNull();
    expect(within(deterministicCard).getByText(UI_COPY.deterministic)).toBeTruthy();
  });

  it("flags low self-reported confidence on the issue card, not when high or absent", async () => {
    const report = buildReport();
    report.issues = [
      { ...buildIssue({ rule_id: "LOWCONF-001", message: "uncertain reading" }), confidence: 0.42 },
      { ...buildIssue({ rule_id: "HIGHCONF-001", message: "clear reading" }), confidence: 0.95 },
      { ...buildIssue({ rule_id: "NOCONF-001", message: "reading without score" }), confidence: null },
    ];
    fetchReportMock.mockResolvedValue(report);

    render(<App />);

    const lowCard = await screen.findByRole("button", { name: /LOWCONF-001/i });
    const highCard = screen.getByRole("button", { name: /HIGHCONF-001/i });
    const noneCard = screen.getByRole("button", { name: /NOCONF-001/i });

    // Low self-reported confidence is surfaced as a review cue (§12), labelled
    // uncalibrated so it is not read as a calibrated probability.
    expect(within(lowCard).getByText(/низкая уверенность/i)).toBeTruthy();
    expect(within(lowCard).getByTitle(/без калибровки/i)).toBeTruthy();
    // High or absent confidence carries no low-confidence warning.
    expect(within(highCard).queryByText(/низкая уверенность/i)).toBeNull();
    expect(within(noneCard).queryByText(/низкая уверенность/i)).toBeNull();
  });

  it("renders REVIEW_REQUIRED as a distinct outcome badge, not a pass/verdict", async () => {
    const report = buildReport();
    report.summary = { ...report.summary, outcome: "review_required", passed: false };
    fetchReportMock.mockResolvedValue(report);

    render(<App />);

    const badges = await screen.findAllByText(/REVIEW_REQUIRED/);
    expect(badges.length).toBeGreaterThan(0);
    for (const badge of badges) {
      expect(badge.className).toContain("outcome-review");
      expect(badge.className).not.toContain("outcome-pass");
      expect(badge.className).not.toContain("outcome-block");
      expect(badge.className).not.toContain("outcome-fail");
    }
  });

  it("renders FAILED as a solid violation badge, distinct from BLOCKED missing-data", async () => {
    const failed = buildReport();
    failed.summary = { ...failed.summary, outcome: "failed", passed: false };
    fetchReportMock.mockResolvedValue(failed);

    const { unmount } = render(<App />);
    const failBadges = await screen.findAllByText(/FAILED —/);
    expect(failBadges.length).toBeGreaterThan(0);
    for (const badge of failBadges) {
      expect(badge.className).toContain("outcome-fail");
      expect(badge.className).not.toContain("outcome-block");
    }
    unmount();

    const blocked = buildReport();
    blocked.summary = { ...blocked.summary, outcome: "blocked", passed: false };
    fetchReportMock.mockResolvedValue(blocked);
    render(<App />);
    const blockBadges = await screen.findAllByText(/BLOCKED —/);
    expect(blockBadges.length).toBeGreaterThan(0);
    for (const badge of blockBadges) {
      expect(badge.className).toContain("outcome-block");
      expect(badge.className).not.toContain("outcome-fail");
    }
  });

  it("lets an expert confirm or reject a remark before export", async () => {
    render(<App />);

    const confirm = await screen.findByRole("button", { name: /подтвердить замечание/i });
    fireEvent.click(confirm);
    await waitFor(() => {
      expect(postReviewEventMock).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ event_type: "opened", issue_rule_id: "DRAW-001" }),
      );
      expect(postReviewEventMock).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ event_type: "accepted", previous_state: "opened" }),
      );
    });
    expect(await screen.findByText("Подтверждено")).toBeTruthy();

    const reject = screen.getByRole("button", { name: /отклонить замечание/i });
    fireEvent.click(reject);
    await waitFor(() => {
      expect(postReviewEventMock).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ event_type: "rejected", previous_state: "accepted" }),
      );
    });
    expect(await screen.findByText("Отклонено")).toBeTruthy();
  });

  it("opens the TZ coverage IA map from workplace nav", async () => {
    render(<App />);
    expect(await screen.findByText("Residential Tower Alpha")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Эффект" }));
    expect(screen.getByTestId("tz-workplace-coverage")).toBeTruthy();
    expect(screen.getByTestId("review-kpi-panel")).toBeTruthy();
    expect(screen.getByTestId("blocker-honesty-panel")).toBeTruthy();
    expect(screen.getByText("SCR-DIFF")).toBeTruthy();
    expect(screen.getAllByText(/«не воспроизведено» ≠ исправлено/).length).toBeGreaterThan(0);
  });

  it("exposes eight workplace screens and a two-report version diff", async () => {
    render(<App />);
    expect(await screen.findByText("Residential Tower Alpha")).toBeTruthy();
    expect(screen.getByTestId("pack-cycle-strip")).toBeTruthy();
    for (const label of [
      "Проекты",
      "Загрузка",
      "Прогон",
      "Эксперт",
      "Замечание",
      "Экспорт",
      "Версии",
      "Эффект",
    ]) {
      expect(screen.getByRole("button", { name: label })).toBeTruthy();
    }
    fireEvent.click(screen.getByRole("button", { name: "Версии" }));
    expect(screen.getByTestId("version-diff-panel")).toBeTruthy();
    expect(screen.getByText(/«Не воспроизведено» ≠ исправлено/)).toBeTruthy();
  });

  it("keeps the report index on Проекты and the TZ three-pane on Эксперт", async () => {
    render(<App />);

    expect(await screen.findByTestId("expert-workplace")).toBeTruthy();
    expect(await screen.findByTestId("machine-human-split")).toBeTruthy();
    expect(screen.getByTestId("expert-findings-pane")).toBeTruthy();
    expect(screen.getByTestId("expert-spatial-pane")).toBeTruthy();
    expect(screen.getByTestId("expert-remark-pane")).toBeTruthy();
    expect(screen.queryByPlaceholderText(UI_COPY.searchReports)).toBeNull();

    openProjectsIndex();
    expect(await screen.findByPlaceholderText(UI_COPY.searchReports)).toBeTruthy();
    expect(screen.queryByTestId("expert-workplace")).toBeNull();
    expect(screen.getByTestId("projects-index")).toBeTruthy();
  });

  it("moves to the next finding with J and confirms with A", async () => {
    render(<App />);
    const viewer = await screen.findByTestId("viewer-stub");
    expect(within(viewer).getByText("DRAW-001")).toBeTruthy();
    fireEvent.keyDown(window, { key: "j" });
    expect(await within(viewer).findByText(UI_COPY.spatialNone)).toBeTruthy();
    fireEvent.keyDown(window, { key: "a" });
    await waitFor(() => {
      expect(postReviewEventMock).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ event_type: "accepted", issue_rule_id: "DRAW-SECOND" }),
      );
    });
  });

  it("treats the header role switch as a screen mock, not HITL access", async () => {
    render(<App />);
    expect(await screen.findByRole("button", { name: /подтвердить замечание/i })).toBeTruthy();
    expect(screen.getByTestId("role-honesty-banner").textContent).toMatch(/не проверяется сервером/);
    fireEvent.change(screen.getByLabelText(UI_COPY.roleSelectLabel), { target: { value: "user" } });
    fireEvent.click(screen.getByRole("button", { name: "Эксперт" }));
    // UI3 P0.4: роль «Пользователь» не видит и не может вызвать правку/подтверждение/отклонение.
    expect(await screen.findByTestId("hitl-readonly-note")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /подтвердить замечание/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /отклонить замечание/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /сохранить правку/i })).toBeNull();
    expect(screen.queryByLabelText(UI_COPY.editRemark)).toBeNull();
  });

  it("hides HITL writes for a LAB viewer session and does not claim SSO", async () => {
    fetchAuthBffMock.mockResolvedValue({ httpStatus: 200, status: "LAB" });
    fetchAuthSessionMock.mockResolvedValue({
      authenticated: true,
      identityVerified: true,
      roles: ["user"],
      tenantId: "tenant-a",
      subject: "viewer-1",
    });
    render(<App />);
    expect(await screen.findByTestId("hitl-readonly-note")).toBeTruthy();
    expect(screen.getByTestId("role-honesty-banner").textContent).toMatch(/не промышленный SSO/);
    expect(screen.getByTestId("role-honesty-banner").textContent).toMatch(/LAB/);
    expect(screen.queryByRole("button", { name: /подтвердить замечание/i })).toBeNull();
    expect((screen.getByLabelText(UI_COPY.roleSelectLabel) as HTMLSelectElement).disabled).toBe(
      true,
    );
    fireEvent.keyDown(window, { key: "a" });
    fireEvent.keyDown(window, { key: "r" });
    expect(postReviewEventMock).not.toHaveBeenCalled();
  });

  it("migrates a legacy team preset chip to JSON file exchange", async () => {
    window.localStorage.setItem(
      REPORT_FILTER_PRESETS_STORAGE_KEY,
      JSON.stringify([
        {
          id: "preset-team",
          name: "Legacy Team",
          scope: "team",
          filters: { project: "hospital", discipline: "mech", status: "passed" },
        },
      ]),
    );
    render(<App />);
    expect(await screen.findByText("Residential Tower Alpha")).toBeTruthy();
    openProjectsIndex();
    expect(screen.getByRole("button", { name: "Legacy Team" })).toBeTruthy();
    expect(screen.getAllByText(UI_COPY.presetFile).length).toBeGreaterThan(0);
    expect(screen.queryByText(/^team$/i)).toBeNull();
  });

  it("lands the git fixture on the expert screen with BCF and the remark card", async () => {
    const seeded = buildReport();
    seeded.report_id = "d".repeat(32);
    seeded.project_name = "Git walls fixture";
    seedDemoFixtureMock.mockResolvedValue({
      fixture: true,
      checkpoint: "GO",
      closes_rt001: false,
      report_id: seeded.report_id,
      issue_count: seeded.issues.length,
      note: "Git fixture",
    });
    fetchReportMock.mockImplementation(async (reportId: string) =>
      reportId === seeded.report_id ? seeded : buildReport(),
    );
    fetchReportsMock.mockResolvedValue({
      reports: [toReportSummary(buildReport()), toReportSummary(seeded)],
      count: 2,
    });
    render(<App />);
    expect(await screen.findByTestId("expert-workplace")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.demoSeed }));
    await waitFor(() => {
      expect((screen.getByLabelText(UI_COPY.selectedPack) as HTMLSelectElement).value).toBe(
        seeded.report_id,
      );
    });
    expect(screen.getByTestId("demo-fixture-panel").getAttribute("data-compact")).toBe("true");
    expect(screen.getByTestId("expert-findings-pane")).toBeTruthy();
    expect(screen.getByTestId("expert-spatial-pane")).toBeTruthy();
    expect(screen.getByTestId("expert-remark-pane")).toBeTruthy();
    expect(screen.getByTestId("remark-card").textContent).toContain(UI_COPY.remarkClause);
    expect(screen.getByTestId("remark-card").textContent).toMatch(/нет в индексе/);
    expect(screen.getByTestId("export-actions")).toBeTruthy();
    expect(screen.getByRole("button", { name: "BCF" })).toBeTruthy();
    expect(screen.getByRole("button", { name: UI_COPY.exportPdf })).toBeTruthy();
    expect(screen.queryByTestId("export-preview")).toBeNull();
  });

  it("walks the commission route upload → run onto the expert screen without extra tabs", async () => {
    const packed = buildReport();
    uploadDocumentMock.mockResolvedValue({
      upload_id: "up-1",
      filename: "walls.ifc",
      path: "uploads/walls.ifc",
      size_bytes: 12,
      content_type: null,
      object_key: null,
    });
    submitAnalyzeProjectPackageMock.mockResolvedValue({
      job_id: "job-kt3",
      status: "succeeded",
      report_id: packed.report_id,
    });
    render(<App />);
    expect(await screen.findByTestId("expert-workplace")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Загрузка" }));
    const input = screen.getByLabelText(UI_COPY.packFileUpload) as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File(["IFC"], "walls.ifc", { type: "application/octet-stream" })] },
    });
    expect(await screen.findByTestId("analyze-run-panel")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Запустить анализ" }));
    expect(await screen.findByTestId("expert-workplace")).toBeTruthy();
    expect(screen.getByTestId("rehearsal-one-click")).toBeTruthy();
    expect(screen.getByTestId("remark-card")).toBeTruthy();
    expect(screen.getByTestId("export-actions")).toBeTruthy();
    expect(screen.getByRole("button", { name: "BCF" })).toBeTruthy();
    expect(screen.getByRole("button", { name: UI_COPY.exportPdf })).toBeTruthy();
    expect(screen.queryByTestId("export-preview")).toBeNull();
  });
});