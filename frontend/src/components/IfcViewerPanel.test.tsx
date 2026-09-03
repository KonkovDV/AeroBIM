import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ValidationReport } from "../lib/types";
import { UI_COPY } from "../lib/ui-copy";

const {
  fetchReportIfcSourceMock,
  loadModelMock,
  getElementPropsMock,
  listStoreysMock,
  setSelectedGuidsMock,
} = vi.hoisted(() => ({
  fetchReportIfcSourceMock: vi.fn(),
  loadModelMock: vi.fn(),
  getElementPropsMock: vi.fn(),
  listStoreysMock: vi.fn(),
  setSelectedGuidsMock: vi.fn(),
}));

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return {
    ...actual,
    fetchReportIfcSource: fetchReportIfcSourceMock,
  };
});

vi.mock("../lib/ifc-scene", () => ({
  IfcSceneController: class {
    init = () => Promise.resolve();
    loadModel = loadModelMock;
    getElementProps = getElementPropsMock;
    listStoreys = listStoreysMock;
    setStoreyFilter = vi.fn();
    setSelectedGuids = setSelectedGuidsMock;
    setIsolateSelection = vi.fn();
    clearModel = vi.fn();
    resetView = vi.fn();
    dispose = vi.fn();
  },
}));

import IfcViewerPanel from "./IfcViewerPanel";

function report(): ValidationReport {
  return {
    report_id: "c".repeat(32),
    request_id: "req",
    created_at: "2026-09-03T00:00:00Z",
    requirements: [],
    issues: [],
    summary: {
      requirement_count: 0,
      issue_count: 0,
      error_count: 0,
      warning_count: 0,
      passed: false,
      drawing_annotation_count: 0,
      generated_remark_count: 0,
    },
    drawing_annotations: [],
    drawing_assets: [],
    clash_results: [],
  };
}

describe("IfcViewerPanel", () => {
  beforeEach(() => {
    fetchReportIfcSourceMock.mockReset();
    loadModelMock.mockReset();
    getElementPropsMock.mockReset();
    listStoreysMock.mockReset();
    setSelectedGuidsMock.mockReset();
    fetchReportIfcSourceMock.mockResolvedValue(new Uint8Array([1, 2, 3]));
    loadModelMock.mockResolvedValue(undefined);
    listStoreysMock.mockReturnValue([{ expressId: 10, name: "3 этаж", guid: "storey-1" }]);
    getElementPropsMock.mockImplementation((guid: string | null) =>
      guid
        ? {
            guid,
            expressId: 1,
            typeName: "IfcWall",
            name: "Wall-1",
            storeyName: "3 этаж",
          }
        : null,
    );
  });

  it("loads IFC once per report_id and refreshes properties when the GUID changes", async () => {
    const selected = report();
    const { rerender } = render(
      <IfcViewerPanel
        report={selected}
        selectedGuids={["guid-a"]}
        selectionMode="issue"
        selectionHeading="FIRE-1"
        selectionDetail="focus"
      />,
    );
    expect(await screen.findByText("Wall-1")).toBeTruthy();
    expect(screen.getByTestId("viewer-element-props").textContent).toMatch(/IfcWall/);
    expect(screen.getByRole("combobox", { name: UI_COPY.storeyFilter })).toBeTruthy();
    expect(fetchReportIfcSourceMock).toHaveBeenCalledTimes(1);
    expect(loadModelMock).toHaveBeenCalledTimes(1);

    rerender(
      <IfcViewerPanel
        report={selected}
        selectedGuids={["guid-b"]}
        selectionMode="issue"
        selectionHeading="FIRE-2"
        selectionDetail="focus"
      />,
    );
    await waitFor(() => {
      expect(getElementPropsMock).toHaveBeenCalledWith("guid-b");
    });
    expect(fetchReportIfcSourceMock).toHaveBeenCalledTimes(1);
    expect(loadModelMock).toHaveBeenCalledTimes(1);
    expect(screen.getByText("guid-b")).toBeTruthy();
  });
});
