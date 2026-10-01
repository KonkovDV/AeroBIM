import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { CheckCoverageMap } from "../lib/api";
import { UI_COPY } from "../lib/ui-copy";
import CoverageMapPanel from "./CoverageMapPanel";

const { fetchReportCoverageMock } = vi.hoisted(() => ({
  fetchReportCoverageMock: vi.fn(),
}));

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return {
    ...actual,
    fetchReportCoverage: fetchReportCoverageMock,
  };
});

function buildMap(overrides: Partial<CheckCoverageMap> = {}): CheckCoverageMap {
  return {
    artifact: "check-coverage",
    schema_version: "1.2.0",
    operator_legend: {
      no_findings: "check ran; no issues",
      findings: "check ran; see issues",
      not_checked: "family not executed",
      insufficient_data: "inputs missing",
      expert_required: "HITL needed",
    },
    tz_gaps: [
      {
        gap_id: "mep_system_clash",
        label: "MEP systems",
        status: "not_checked",
        reason: "TZ matrix hole",
      },
    ],
    sources: [
      {
        source_id: "model.ifc",
        families: { geometry: "no_findings", mep: "not_checked" },
        operator_status: { geometry: "no_findings", mep: "not_checked" },
        presentation_status: { geometry: "no_findings", mep: "not_checked" },
        reasons: { mep: "no MEP discipline package" },
      },
      {
        source_id: "sheet.pdf",
        families: { drawing: "findings" },
        operator_status: { drawing: "findings" },
        presentation_status: { drawing: "findings" },
        reasons: { drawing: "DRAW-001" },
      },
    ],
    ...overrides,
  };
}

describe("CoverageMapPanel", () => {
  beforeEach(() => {
    fetchReportCoverageMock.mockReset();
  });

  it("shows loading copy before coverage arrives", () => {
    fetchReportCoverageMock.mockReturnValue(new Promise(() => undefined));
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    expect(screen.getByText(/загрузка/i)).toBeTruthy();
  });

  it("renders honesty note that coverage is not the package verdict", async () => {
    fetchReportCoverageMock.mockResolvedValue(buildMap());
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    await screen.findByTestId("coverage-map");
    expect(screen.getByText(/не итог комплекта/i)).toBeTruthy();
    expect(screen.queryByText(/summary\.passed/i)).toBeNull();
  });

  it("renders TZ gaps as not checked, never as no findings", async () => {
    fetchReportCoverageMock.mockResolvedValue(buildMap());
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    const gaps = await screen.findByTestId("coverage-tz-gaps");
    expect(gaps.querySelector('[data-coverage-status="not_checked"]')).toBeTruthy();
    expect(gaps.textContent).toMatch(/не проверялось/i);
    expect(gaps.textContent).not.toMatch(/no_findings/);
  });

  it("lists operator legend in Russian for the five honest states", async () => {
    fetchReportCoverageMock.mockResolvedValue(buildMap());
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    await screen.findByTestId("coverage-map");
    expect(screen.getAllByText(UI_COPY.covFilterNoFindings).length).toBeGreaterThan(0);
    expect(screen.getAllByText(UI_COPY.covFilterFindings).length).toBeGreaterThan(0);
    expect(screen.getAllByText(UI_COPY.covFilterNotChecked).length).toBeGreaterThan(0);
    expect(screen.getAllByText(UI_COPY.covFilterInsufficient).length).toBeGreaterThan(0);
    expect(screen.getAllByText(UI_COPY.covFilterExpert).length).toBeGreaterThan(0);
  });

  it("renders per-source family cells from presentation_status", async () => {
    fetchReportCoverageMock.mockResolvedValue(buildMap());
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    await screen.findByText("model.ifc");
    expect(screen.getByText("sheet.pdf")).toBeTruthy();
    expect(screen.getAllByText(UI_COPY.covFilterNoFindings).length).toBeGreaterThan(0);
    expect(screen.getAllByText(UI_COPY.covFilterFindings).length).toBeGreaterThan(0);
  });

  it("filters rows by selected operator status", async () => {
    fetchReportCoverageMock.mockResolvedValue(buildMap());
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    await screen.findByText("model.ifc");
    fireEvent.change(screen.getByTestId("coverage-status-filter"), {
      target: { value: "findings" },
    });
    expect(screen.queryByText("model.ifc")).toBeNull();
    expect(screen.getByText("sheet.pdf")).toBeTruthy();
  });

  it("shows empty-filter copy when no rows match", async () => {
    fetchReportCoverageMock.mockResolvedValue(buildMap());
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    await screen.findByText("model.ifc");
    fireEvent.change(screen.getByTestId("coverage-status-filter"), {
      target: { value: "expert_required" },
    });
    expect(screen.getByText(/нет строк для выбранного фильтра/i)).toBeTruthy();
  });

  it("invokes onNavigateToFindings from findings cells", async () => {
    const onNavigate = vi.fn();
    fetchReportCoverageMock.mockResolvedValue(buildMap());
    render(<CoverageMapPanel reportId={"r".repeat(32)} onNavigateToFindings={onNavigate} />);
    const link = await screen.findByRole("button", { name: UI_COPY.covFindingsLink });
    fireEvent.click(link);
    expect(onNavigate).toHaveBeenCalledTimes(1);
  });

  it("shows unavailable honesty copy when fetch fails", async () => {
    fetchReportCoverageMock.mockRejectedValue(new Error("coverage down"));
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    await waitFor(() => {
      expect(screen.getByText(/coverage down/i)).toBeTruthy();
    });
    expect(screen.getByText(/нет карты/i)).toBeTruthy();
  });

  it("falls back to families when operator_status is absent", async () => {
    fetchReportCoverageMock.mockResolvedValue(
      buildMap({
        sources: [
          {
            source_id: "legacy.ifc",
            families: { geometry: "insufficient_data" },
          },
        ],
        tz_gaps: [],
      }),
    );
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    await screen.findByText("legacy.ifc");
    expect(screen.getAllByText(UI_COPY.covFilterInsufficient).length).toBeGreaterThan(0);
  });

  it("refetches when reportId changes", async () => {
    fetchReportCoverageMock
      .mockResolvedValueOnce(buildMap({ sources: [{ source_id: "a.ifc", families: {} }] }))
      .mockResolvedValueOnce(buildMap({ sources: [{ source_id: "b.ifc", families: {} }] }));
    const { rerender } = render(<CoverageMapPanel reportId={"a".repeat(32)} />);
    await screen.findByText("a.ifc");
    rerender(<CoverageMapPanel reportId={"b".repeat(32)} />);
    await screen.findByText("b.ifc");
    expect(fetchReportCoverageMock).toHaveBeenCalledTimes(2);
  });

  it("renders reason text beside not_checked cells", async () => {
    fetchReportCoverageMock.mockResolvedValue(buildMap());
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    await screen.findByText(/no MEP discipline package/i);
  });

  it("does not render an empty coverage table as success", async () => {
    fetchReportCoverageMock.mockResolvedValue(buildMap({ sources: [], tz_gaps: [] }));
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    expect(await screen.findByText(UI_COPY.covNoSources)).toBeTruthy();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("keeps TZ-gap rows when sources are empty", async () => {
    fetchReportCoverageMock.mockResolvedValue(buildMap({ sources: [] }));
    render(<CoverageMapPanel reportId={"r".repeat(32)} />);
    expect(await screen.findByText(UI_COPY.covNoSources)).toBeTruthy();
    expect(screen.getByTestId("coverage-tz-gaps")).toBeTruthy();
    expect(screen.queryByText("model.ifc")).toBeNull();
  });
});
