import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import RoleHonestyBanner from "./RoleHonestyBanner";

describe("RoleHonestyBanner", () => {
  it("says the header switch is not OIDC access control", () => {
    render(<RoleHonestyBanner />);
    const banner = screen.getByTestId("role-honesty-banner");
    expect(banner.textContent).toMatch(/не разграничение доступа/);
    expect(banner.textContent).toMatch(/501/);
    expect(banner.textContent).toMatch(/403/);
    expect(banner.textContent).not.toMatch(/OIDC live/i);
  });

  it("describes LAB as not customer SSO", () => {
    render(<RoleHonestyBanner bffStatus="LAB" />);
    const banner = screen.getByTestId("role-honesty-banner");
    expect(banner.textContent).toMatch(/LAB/);
    expect(banner.textContent).toMatch(/не промышленный SSO/);
    expect(banner.textContent).toMatch(/403/);
    expect(banner.textContent).not.toMatch(/OIDC live/i);
    expect(banner.textContent).not.toMatch(/501/);
  });

  it("keeps expert actions closed while discovery is loading", () => {
    render(<RoleHonestyBanner bffStatus="LOADING" />);
    const banner = screen.getByTestId("role-honesty-banner");
    expect(banner.textContent).toMatch(/Проверяем сессию/);
    expect(banner.textContent).not.toMatch(/501/);
  });

  it("does not treat UNKNOWN as a demo expert", () => {
    render(<RoleHonestyBanner bffStatus="UNKNOWN" />);
    const banner = screen.getByTestId("role-honesty-banner");
    expect(banner.textContent).toMatch(/Не удалось проверить права/);
    expect(banner.textContent).toMatch(/не открывает запись/);
  });
});
