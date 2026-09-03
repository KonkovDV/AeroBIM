import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ExportActionsBar from "./ExportActionsBar";
import { UI_COPY } from "../../lib/ui-copy";

vi.mock("../../lib/api", () => ({
  downloadExport: vi.fn(),
}));

describe("ExportActionsBar", () => {
  it("exposes html json bcf and pdf; xlsx is not rendered at all", () => {
    render(<ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />);
    const bar = screen.getByTestId("export-actions");
    expect(bar.querySelector("button")?.textContent).toBeTruthy();
    expect(screen.getByRole("button", { name: "HTML" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "JSON" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "BCF" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "BCF 3.0" })).toBeTruthy();
    expect(screen.getByRole("button", { name: UI_COPY.exportPdf })).toBeTruthy();
    // UI3 P0.2: XLSX не рендерим вовсе — эндпоинта нет, фальшивый успех хуже отсутствия.
    expect(screen.queryByRole("button", { name: /XLSX/i })).toBeNull();
  });
});
