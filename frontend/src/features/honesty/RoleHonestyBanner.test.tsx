import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import RoleHonestyBanner from "./RoleHonestyBanner";

describe("RoleHonestyBanner", () => {
  it("says the header switch is not access control without service codes", () => {
    render(<RoleHonestyBanner />);
    const banner = screen.getByTestId("role-honesty-banner");
    expect(banner.textContent).toContain("не предоставляет права доступа");
    expect(banner.textContent).toContain("Демонстрационный режим");
    expect(banner.textContent).not.toMatch(/501|403|OIDC live/i);
  });

  it("describes the laboratory session as not a production login", () => {
    render(<RoleHonestyBanner bffStatus="LAB" />);
    const banner = screen.getByTestId("role-honesty-banner");
    expect(banner.textContent).toContain("Лабораторный режим");
    expect(banner.textContent).toContain("Промышленный вход ещё не подключён");
    expect(banner.textContent).toContain("подтверждённой сессией эксперта");
    expect(banner.textContent).not.toMatch(/OIDC live|501|403/i);
  });

  it("keeps expert actions closed while discovery is loading", () => {
    render(<RoleHonestyBanner bffStatus="LOADING" />);
    const banner = screen.getByTestId("role-honesty-banner");
    expect(banner.textContent).toMatch(/Проверяем сессию/);
    expect(banner.textContent).toContain("Редактирование пока недоступно");
    expect(banner.textContent).not.toMatch(/501/);
  });

  it("does not treat UNKNOWN as a demo expert", () => {
    render(<RoleHonestyBanner bffStatus="UNKNOWN" />);
    const banner = screen.getByTestId("role-honesty-banner");
    expect(banner.textContent).toMatch(/Не удалось проверить права/);
    expect(banner.textContent).toContain("Редактирование недоступно");
  });
});
