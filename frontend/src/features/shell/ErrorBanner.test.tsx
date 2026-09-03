import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ErrorBanner from "./ErrorBanner";
import { UI_COPY } from "../../lib/ui-copy";

describe("ErrorBanner", () => {
  it("shows the failure and retries on click", () => {
    const onRetry = vi.fn();
    render(<ErrorBanner message="API down" onRetry={onRetry} />);
    expect(screen.getByTestId("error-banner").textContent).toMatch(/API down/);
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.retry }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
