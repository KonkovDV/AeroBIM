import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("./wasm-cap", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./wasm-cap")>();
  return {
    ...actual,
    WASM_IFC_VIEWER_CAP_BYTES: 64,
  };
});

import { fetchReportIfcSource } from "./api";
import { IfcViewerCapError, WASM_IFC_VIEWER_CAP_BYTES } from "./wasm-cap";

describe("fetchReportIfcSource viewer cap", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uses a tiny cap in this file so tests do not allocate 256 MiB", () => {
    expect(WASM_IFC_VIEWER_CAP_BYTES).toBe(64);
  });

  it("aborts the body when Content-Length exceeds the viewer cap", async () => {
    const abortSpy = vi.fn();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: string, init?: RequestInit) => {
        init?.signal?.addEventListener("abort", abortSpy);
        return new Response(new Uint8Array([1, 2, 3]), {
          status: 200,
          headers: {
            "content-length": String(WASM_IFC_VIEWER_CAP_BYTES + 1),
            "content-type": "application/octet-stream",
          },
        });
      }),
    );
    await expect(fetchReportIfcSource("c".repeat(32))).rejects.toBeInstanceOf(IfcViewerCapError);
    expect(abortSpy).toHaveBeenCalled();
  });

  it("stops streaming when the body exceeds the cap without Content-Length", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        const stream = new ReadableStream<Uint8Array>({
          start(controller) {
            controller.enqueue(new Uint8Array(WASM_IFC_VIEWER_CAP_BYTES + 8));
            controller.close();
          },
        });
        return new Response(stream, {
          status: 200,
          headers: { "content-type": "application/octet-stream" },
        });
      }),
    );
    await expect(fetchReportIfcSource("c".repeat(32))).rejects.toBeInstanceOf(IfcViewerCapError);
  });

  it("loads a body within the viewer cap", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(new Uint8Array([9, 8, 7]), {
            status: 200,
            headers: {
              "content-length": "3",
              "content-type": "application/octet-stream",
            },
          }),
      ),
    );
    const bytes = await fetchReportIfcSource("c".repeat(32));
    expect(Array.from(bytes)).toEqual([9, 8, 7]);
  });
});
