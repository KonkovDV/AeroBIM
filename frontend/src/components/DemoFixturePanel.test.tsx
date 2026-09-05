import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { seedDemoFixtureMock, labDemoEnabled } = vi.hoisted(() => ({
  seedDemoFixtureMock: vi.fn(),
  labDemoEnabled: vi.fn(() => true),
}));

vi.mock("../lib/api", () => ({
  seedDemoFixture: seedDemoFixtureMock,
}));

vi.mock("../lib/lab-demo", () => ({
  isLabDemoSeedUiEnabled: () => labDemoEnabled(),
}));

import DemoFixturePanel from "./DemoFixturePanel";
import { UI_COPY } from "../lib/ui-copy";

describe("DemoFixturePanel", () => {
  beforeEach(() => {
    labDemoEnabled.mockReset();
    labDemoEnabled.mockReturnValue(true);
    seedDemoFixtureMock.mockReset();
    seedDemoFixtureMock.mockResolvedValue({
      fixture: true,
      checkpoint: "GO",
      closes_rt001: false,
      report_id: "c".repeat(32),
      issue_count: 3,
      note: "Git fixture",
    });
  });

  it("seeds the git fixture and returns the server report id", async () => {
    const onSeeded = vi.fn();
    render(<DemoFixturePanel onSeeded={onSeeded} />);
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.demoSeed }));
    await waitFor(() => {
      expect(seedDemoFixtureMock).toHaveBeenCalledTimes(1);
      expect(onSeeded).toHaveBeenCalledWith("c".repeat(32));
    });
    expect(screen.getByText(/3 находок/)).toBeTruthy();
    expect(screen.getByText(/checkpoint GO/)).toBeTruthy();
    expect(screen.getByTestId("demo-fixture-panel").getAttribute("data-compact")).toBe("true");
  });

  it("hides the essay when the expert already has a report", () => {
    render(<DemoFixturePanel onSeeded={vi.fn()} hideIntro />);
    expect(screen.getByTestId("demo-fixture-panel").getAttribute("data-compact")).toBe("true");
    expect(screen.queryByText(UI_COPY.demoBody)).toBeNull();
    expect(screen.getByRole("button", { name: UI_COPY.demoSeed })).toBeTruthy();
  });

  it("renders nothing when the lab demo gate is off (production)", () => {
    labDemoEnabled.mockReturnValue(false);
    render(<DemoFixturePanel onSeeded={vi.fn()} />);
    expect(screen.queryByTestId("demo-fixture-panel")).toBeNull();
    expect(screen.queryByRole("button", { name: UI_COPY.demoSeed })).toBeNull();
  });
});
