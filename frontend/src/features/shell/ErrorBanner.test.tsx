import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ErrorBanner from "./ErrorBanner";
import { UI_COPY } from "../../lib/ui-copy";

describe("ErrorBanner", () => {
  it("shows recovery instructions and retries without exposing raw diagnostics", () => {
    const onRetry = vi.fn();
    render(<ErrorBanner message="API down: http://private-host/v1; secret=example; trace stack" onRetry={onRetry} />);
    const banner = screen.getByRole("alert");
    expect(banner.textContent).toContain("Не удалось получить данные");
    expect(banner.textContent).not.toMatch(/API down|private-host|secret=|trace stack/);
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.retry }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
