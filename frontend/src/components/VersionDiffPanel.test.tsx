import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import VersionDiffPanel from "./VersionDiffPanel";
import { UI_COPY } from "../lib/ui-copy";

describe("VersionDiffPanel", () => {
  it("asks for two reports and does not claim resolved", () => {
    render(<VersionDiffPanel reports={[]} />);
    expect(screen.getByTestId("version-diff-panel")).toBeTruthy();
    expect(screen.getByText(UI_COPY.diffNote)).toBeTruthy();
    expect(UI_COPY.diffNote).toContain("не доказывает исправление");
    expect(screen.getByText(/Нужны два сохранённых отчёта/)).toBeTruthy();
  });
});
