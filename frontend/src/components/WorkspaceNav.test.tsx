import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import WorkspaceNav, { WORKSPACE_NAV } from "./WorkspaceNav";

describe("WorkspaceNav", () => {
  it("renders eight TZ screens and reports the clicked view", () => {
    const onChange = vi.fn();
    render(<WorkspaceNav workspaceView="review" onChange={onChange} />);
    expect(WORKSPACE_NAV).toHaveLength(8);
    for (const { label } of WORKSPACE_NAV) {
      expect(screen.getByRole("button", { name: label })).toBeTruthy();
    }
    fireEvent.click(screen.getByRole("button", { name: "Загрузка" }));
    expect(onChange).toHaveBeenCalledWith("upload");
  });
});
