import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import IfcViewerErrorBoundary from "./IfcViewerErrorBoundary";

function ThrowOnRender(): never {
  throw new Error("simulated WASM render panic");
}

function Fine() {
  return <div data-testid="fine">ok</div>;
}

describe("IfcViewerErrorBoundary", () => {
  it("renders children when there is no error", () => {
    render(
      <IfcViewerErrorBoundary>
        <Fine />
      </IfcViewerErrorBoundary>,
    );
    expect(screen.getByTestId("fine")).toBeTruthy();
  });

  it("shows fallback instead of crashing on render error", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <IfcViewerErrorBoundary>
        <ThrowOnRender />
      </IfcViewerErrorBoundary>,
    );
    expect(screen.getByTestId("ifc-viewer-error-boundary")).toBeTruthy();
    expect(screen.getByRole("alert")).toBeTruthy();
    spy.mockRestore();
  });

  it("fallback does not leak the raw error message to the DOM", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <IfcViewerErrorBoundary>
        <ThrowOnRender />
      </IfcViewerErrorBoundary>,
    );
    expect(screen.queryByText(/simulated WASM render panic/)).toBeNull();
    spy.mockRestore();
  });
});
