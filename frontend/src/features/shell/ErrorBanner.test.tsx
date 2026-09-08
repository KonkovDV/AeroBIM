import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ErrorBanner from "./ErrorBanner";
import { UI_COPY } from "../../lib/ui-copy";

describe("ErrorBanner", () => {
  it("shows recovery instructions and retries without exposing raw diagnostics", () => {
    const onRetry = vi.fn();
    render(<ErrorBanner kind="unknown" onRetry={onRetry} />);
    const banner = screen.getByRole("alert");
    expect(banner.textContent).toContain("Не удалось получить данные");
    expect(banner.textContent).not.toMatch(/API down|private-host|secret=|trace stack|http/);
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.retry }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("distinguishes forbidden from a network failure", () => {
    const { rerender } = render(<ErrorBanner kind="forbidden" onRetry={() => undefined} />);
    const forbidden = screen.getByRole("alert").textContent ?? "";
    expect(forbidden).toContain("Недостаточно прав");
    rerender(<ErrorBanner kind="network" onRetry={() => undefined} />);
    const network = screen.getByRole("alert").textContent ?? "";
    expect(network).toContain("Нет связи");
    expect(network).not.toBe(forbidden);
    expect(network).not.toMatch(/http|localhost|stack/i);
  });
});
