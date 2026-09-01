import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const uploadDocumentMock = vi.fn();

vi.mock("../lib/api", () => ({
  uploadDocument: (...args: unknown[]) => uploadDocumentMock(...args),
}));

import PackUploadPanel from "./PackUploadPanel";

describe("PackUploadPanel", () => {
  beforeEach(() => {
    uploadDocumentMock.mockReset();
  });

  it("does not upload native RVT and shows fail-closed copy", async () => {
    render(<PackUploadPanel />);
    const input = screen.getByLabelText("Pack file upload") as HTMLInputElement;
    const file = new File(["x"], "tower.rvt", { type: "application/octet-stream" });
    fireEvent.change(input, { target: { files: [file] } });
    const honesty = await screen.findByTestId("pack-kind-honesty");
    expect(honesty.textContent).toMatch(/Fail-closed/i);
    expect(uploadDocumentMock).not.toHaveBeenCalled();
    expect(screen.getByTestId("pack-dropzone")).toBeTruthy();
  });
});
