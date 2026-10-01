import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import WorkspaceNav from "./WorkspaceNav";
import { UI_COPY } from "../lib/ui-copy";

describe("product workspace navigation", () => {
  it("offers every destination through a labelled native mobile selector", () => {
    const onChange = vi.fn();
    render(<WorkspaceNav workspaceView="review" onChange={onChange} />);
    const select = screen.getByLabelText("Раздел рабочего места") as HTMLSelectElement;
    expect(select.options.length).toBe(8);
    expect(select.value).toBe("review");
    fireEvent.change(select, { target: { value: "diff" } });
    expect(onChange).toHaveBeenCalledWith("diff");
  });

  it("describes the full finding count without changing the button name", () => {
    render(<WorkspaceNav workspaceView="review" onChange={() => undefined} reviewFindingsCount={120} />);
    const button = screen.getByRole("button", { name: UI_COPY.navReview });
    expect(button.getAttribute("aria-current")).toBe("page");
    expect(button.getAttribute("aria-keyshortcuts")).toBe("Alt+4");
    const description = button.getAttribute("aria-describedby");
    expect(description).toBeTruthy();
    expect(document.getElementById(description!)?.textContent).toBe(UI_COPY.navReviewCount(120));
    expect(screen.getByTestId("nav-review-badge").textContent).toBe("99+");
    expect(screen.getByTestId("nav-review-badge").getAttribute("aria-hidden")).toBe("true");
  });

  it("does not hijack a native selector or a text field", () => {
    const onChange = vi.fn();
    render(<><WorkspaceNav workspaceView="review" onChange={onChange} /><textarea aria-label="Текст замечания" /></>);
    fireEvent.keyDown(screen.getByLabelText("Раздел рабочего места"), { key: "2", altKey: true });
    fireEvent.keyDown(screen.getByLabelText("Текст замечания"), { key: "2", altKey: true });
    expect(onChange).not.toHaveBeenCalled();
    fireEvent.keyDown(window, { key: "2", altKey: true });
    expect(onChange).toHaveBeenCalledWith("upload");
  });
});
