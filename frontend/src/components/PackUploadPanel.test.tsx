import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const uploadDocumentMock = vi.fn();

vi.mock("../lib/api", () => ({
  uploadDocument: (...args: unknown[]) => uploadDocumentMock(...args),
}));

import PackUploadPanel from "./PackUploadPanel";
import { UI_COPY } from "../lib/ui-copy";

describe("PackUploadPanel", () => {
  beforeEach(() => {
    uploadDocumentMock.mockReset();
  });

  it("does not upload native RVT and shows fail-closed copy", async () => {
    render(<PackUploadPanel />);
    const input = screen.getByLabelText(UI_COPY.packFileUpload) as HTMLInputElement;
    const file = new File(["x"], "tower.rvt", { type: "application/octet-stream" });
    fireEvent.change(input, { target: { files: [file] } });
    const honesty = await screen.findByTestId("pack-kind-honesty");
    expect(honesty.textContent).toMatch(/Fail-closed/i);
    expect(uploadDocumentMock).not.toHaveBeenCalled();
    expect(screen.getByTestId("pack-dropzone")).toBeTruthy();
  });

  it("cancels an in-flight upload via AbortSignal", async () => {
    let capturedSignal: AbortSignal | undefined;
    uploadDocumentMock.mockImplementation(
      (_file: File, options?: { signal?: AbortSignal }) =>
        new Promise((_resolve, reject) => {
          capturedSignal = options?.signal;
          options?.signal?.addEventListener("abort", () => {
            reject(new Error("Upload cancelled"));
          });
        }),
    );
    render(<PackUploadPanel />);
    const input = screen.getByLabelText(UI_COPY.packFileUpload) as HTMLInputElement;
    const file = new File(["IFC"], "walls.ifc", { type: "application/octet-stream" });
    fireEvent.change(input, { target: { files: [file] } });
    const cancel = await screen.findByRole("button", { name: UI_COPY.cancelUpload });
    fireEvent.click(cancel);
    expect(capturedSignal?.aborted).toBe(true);
    expect(await screen.findByText("Upload cancelled")).toBeTruthy();
  });

  it("shows a draft-slot replacement note when the parent reports one", () => {
    render(<PackUploadPanel draftApplyNote="Слот IFC заменён (было models/a.ifc)." />);
    expect(screen.getByTestId("pack-draft-apply-note").textContent).toMatch(/заменён/);
  });
});
