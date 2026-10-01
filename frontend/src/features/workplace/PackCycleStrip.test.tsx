import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import PackCycleStrip from "./PackCycleStrip";
import { EMPTY_PACK_DRAFT } from "../../lib/pack-draft";

describe("PackCycleStrip", () => {
  it("keeps run blocked until a pack file exists and advances to upload", () => {
    const onChange = vi.fn();
    render(
      <PackCycleStrip
        workspaceView="projects"
        packDraft={EMPTY_PACK_DRAFT}
        hasReport={false}
        onChange={onChange}
      />,
    );
    expect(screen.getByTestId("pack-cycle-strip")).toBeTruthy();
    expect(
      (screen.getByRole("button", { name: "Цикл: запуск анализа" }) as HTMLButtonElement).disabled,
    ).toBe(true);
    expect(
      (screen.getByRole("button", { name: "Цикл: триаж находок" }) as HTMLButtonElement).disabled,
    ).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Цикл: приём файлов" }));
    expect(onChange).toHaveBeenCalledWith("upload");
  });

  it("opens the expert step when a report exists", () => {
    const onChange = vi.fn();
    render(
      <PackCycleStrip
        workspaceView="export"
        packDraft={{ ...EMPTY_PACK_DRAFT, ifcPath: "walls.ifc" }}
        hasReport
        onChange={onChange}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Цикл: триаж находок" }));
    expect(onChange).toHaveBeenCalledWith("review");
  });

  it("opens TZ coverage without waiting for a report", () => {
    const onChange = vi.fn();
    render(
      <PackCycleStrip
        workspaceView="projects"
        packDraft={EMPTY_PACK_DRAFT}
        hasReport={false}
        onChange={onChange}
      />,
    );
    const coverage = screen.getByRole("button", { name: "Цикл: карта покрытия ТЗ" }) as HTMLButtonElement;
    expect(coverage.disabled).toBe(false);
    fireEvent.click(coverage);
    expect(onChange).toHaveBeenCalledWith("user");
  });
});
