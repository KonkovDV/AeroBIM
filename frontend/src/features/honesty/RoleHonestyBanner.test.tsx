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
});
