import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import VersionDiffPanel from "./VersionDiffPanel";

describe("VersionDiffPanel", () => {
  it("asks for two reports and does not claim resolved", () => {
    render(<VersionDiffPanel reports={[]} />);
    expect(screen.getByTestId("version-diff-panel")).toBeTruthy();
    expect(screen.getByText(/«Не воспроизведено» ≠ исправлено/)).toBeTruthy();
    expect(screen.getByText(/Нужны два сохранённых отчёта/)).toBeTruthy();
  });
});
