import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import EvidenceDeck from "./EvidenceDeck";
import { UI_COPY } from "../../lib/ui-copy";

describe("EvidenceDeck", () => {
  it("opens the model and reveals one archive surface at a time", () => {
    render(
      <EvidenceDeck
        model={<p>model-surface</p>}
        drawing={<p>drawing-surface</p>}
        clash={<p>clash-surface</p>}
      />,
    );

    const panel = (label: string) => screen.getByText(label).closest(".evidence-deck-panel");

    expect(screen.getByRole("tab", { name: UI_COPY.evidenceTabModel, selected: true })).toBeTruthy();
    expect(panel("model-surface")?.hasAttribute("hidden")).toBe(false);
    expect(panel("drawing-surface")?.hasAttribute("hidden")).toBe(true);
    expect(panel("clash-surface")?.hasAttribute("hidden")).toBe(true);

    fireEvent.click(screen.getByRole("tab", { name: UI_COPY.evidenceTabDrawing }));
    expect(panel("drawing-surface")?.hasAttribute("hidden")).toBe(false);
    expect(panel("model-surface")?.hasAttribute("hidden")).toBe(true);

    fireEvent.click(screen.getByRole("tab", { name: UI_COPY.evidenceTabClash }));
    expect(panel("clash-surface")?.hasAttribute("hidden")).toBe(false);
    expect(panel("drawing-surface")?.hasAttribute("hidden")).toBe(true);
    expect(panel("clash-surface")?.getAttribute("tabindex")).toBe("0");
  });

  it("toggles the center expansion without leaving the evidence surfaces", () => {
    const onToggleExpanded = vi.fn();
    render(
      <EvidenceDeck
        model={<p>model-surface</p>}
        drawing={<p>drawing-surface</p>}
        clash={<p>clash-surface</p>}
        expanded={false}
        onToggleExpanded={onToggleExpanded}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.expandCenter }));
    expect(onToggleExpanded).toHaveBeenCalledOnce();
  });
});
