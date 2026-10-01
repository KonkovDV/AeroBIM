/** Browser WASM/SPF cap. Disk ingest up to 1.5 GB is not a viewer budget. */

export const WASM_IFC_VIEWER_CAP_BYTES = 256 * 1024 * 1024;

export class IfcViewerCapError extends Error {
  readonly code = "IFC_VIEWER_CAP" as const;

  constructor(message = "") {
    super(message);
    this.name = "IfcViewerCapError";
  }
}

export function ifcExceedsViewerCap(byteLength: number): boolean {
  return byteLength > WASM_IFC_VIEWER_CAP_BYTES;
}

export function assertFitsIfcViewerCap(byteLength: number): void {
  if (ifcExceedsViewerCap(byteLength)) {
    throw new IfcViewerCapError();
  }
}
