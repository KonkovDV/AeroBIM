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

  it("shows the selected-report findings badge only when a count is given", () => {
    const { rerender } = render(<WorkspaceNav workspaceView="review" onChange={() => undefined} />);
    expect(screen.queryByTestId("nav-review-badge")).toBeNull();
    rerender(
      <WorkspaceNav workspaceView="projects" onChange={() => undefined} reviewFindingsCount={7} />,
    );
    const badge = screen.getByTestId("nav-review-badge");
    expect(badge.textContent).toBe("7");
    // aria-hidden: доступное имя кнопки «Эксперт» не меняется.
    expect(badge.getAttribute("aria-hidden")).toBe("true");
    expect(screen.getByRole("button", { name: "Эксперт" })).toBeTruthy();
  });
});
