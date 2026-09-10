import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ShellHeader from "./ShellHeader";
import { UI_COPY } from "../../lib/ui-copy";

describe("product header", () => {
  it("keeps access limitations visible without service addresses or debugging copy", () => {
    const onRoleChange = vi.fn();
    const { container } = render(<ShellHeader apiBase="https://internal.example/v1" reportCount={3}
      uiRole="expert" onRoleChange={onRoleChange} bffStatus="NOT_IMPLEMENTED" />);
    expect(container.textContent).not.toMatch(/internal\.example|summary\.passed|customer_go|checkpoint|review-events|Bearer|GET \/v1/);
    expect(screen.getByTestId("role-honesty-banner").textContent).toContain("не предоставляет права доступа");
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(UI_COPY.headerTitle);
    fireEvent.change(screen.getByRole("combobox", { name: UI_COPY.roleSelectLabel }), { target: { value: "user" } });
    expect(onRoleChange).toHaveBeenCalledWith("user");
    expect(container.querySelector("details")?.open).toBe(false);
    expect(container.querySelector("details")?.textContent).toContain("Внедрение у заказчика ещё не подтверждено");
  });
  it("preserves the server-locked role and announces unavailable permissions", () => {
    render(<ShellHeader apiBase="" reportCount={0} uiRole="user" onRoleChange={() => undefined}
      bffStatus="UNKNOWN" roleLocked />);
    expect((screen.getByRole("combobox", { name: UI_COPY.roleSelectLabel }) as HTMLSelectElement).disabled).toBe(true);
    expect(screen.getByRole("note").textContent).toContain("Редактирование недоступно");
  });
});
