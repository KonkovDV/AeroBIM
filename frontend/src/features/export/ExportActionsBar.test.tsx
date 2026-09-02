import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ExportActionsBar from "./ExportActionsBar";
import { UI_COPY } from "../../lib/ui-copy";

vi.mock("../../lib/api", () => ({
  downloadExport: vi.fn(),
}));

describe("ExportActionsBar", () => {
  it("exposes html json bcf and pdf without enabling xlsx", () => {
    render(<ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />);
    const bar = screen.getByTestId("export-actions");
    expect(bar.querySelector("button")?.textContent).toBeTruthy();
    expect(screen.getByRole("button", { name: "HTML" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "JSON" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "BCF", exact: true })).toBeTruthy();
    expect(screen.getByRole("button", { name: "BCF 3.0", exact: true })).toBeTruthy();
    expect(screen.getByRole("button", { name: UI_COPY.exportPdf })).toBeTruthy();
    expect((screen.getByRole("button", { name: UI_COPY.xlsxNotMvp }) as HTMLButtonElement).disabled).toBe(
      true,
    );
  });
});
