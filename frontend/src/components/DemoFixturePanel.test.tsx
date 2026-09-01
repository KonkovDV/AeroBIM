import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { seedDemoFixtureMock } = vi.hoisted(() => ({
  seedDemoFixtureMock: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  seedDemoFixture: seedDemoFixtureMock,
}));

import DemoFixturePanel from "./DemoFixturePanel";

describe("DemoFixturePanel", () => {
  beforeEach(() => {
    seedDemoFixtureMock.mockReset();
    seedDemoFixtureMock.mockResolvedValue({
      fixture: true,
      checkpoint: "NO_GO",
      closes_rt001: false,
      report_id: "c".repeat(32),
      issue_count: 3,
      note: "Git fixture",
    });
  });

  it("seeds the git fixture and returns the server report id", async () => {
    const onSeeded = vi.fn();
    render(<DemoFixturePanel onSeeded={onSeeded} />);
    fireEvent.click(screen.getByRole("button", { name: /Загрузить демонстрационный комплект/ }));
    await waitFor(() => {
      expect(seedDemoFixtureMock).toHaveBeenCalledTimes(1);
      expect(onSeeded).toHaveBeenCalledWith("c".repeat(32));
    });
    expect(screen.getByText(/3 находок/)).toBeTruthy();
    expect(screen.getByText(/checkpoint NO_GO/)).toBeTruthy();
  });
});
