/** Pack kind from filename. Not a product capability matrix. */

export type PackKind =
  | "ifc"
  | "ids"
  | "pdf"
  | "office"
  | "dxf"
  | "dwg"
  | "rvt"
  | "nwd"
  | "lir"
  | "zip"
  | "other";

export type PackKindVerdict = "upload_ok" | "fail_closed";

const FAIL_CLOSED: ReadonlySet<PackKind> = new Set(["dwg", "rvt", "nwd", "lir"]);

export function detectPackKind(filename: string): PackKind {
  const lower = filename.trim().toLowerCase();
  const dot = lower.lastIndexOf(".");
  const ext = dot >= 0 ? lower.slice(dot) : "";
  if (ext === ".ifc" || ext === ".ifczip") return "ifc";
  if (ext === ".ids") return "ids";
  if (ext === ".pdf") return "pdf";
  if (ext === ".xlsx" || ext === ".xlsm" || ext === ".docx" || ext === ".doc") return "office";
  if (ext === ".dxf") return "dxf";
  if (ext === ".dwg") return "dwg";
  if (ext === ".rvt" || ext === ".rte") return "rvt";
  if (ext === ".nwd" || ext === ".nwc") return "nwd";
  if (ext === ".lir" || ext === ".spr") return "lir";
  if (ext === ".zip") return "zip";
  return "other";
}

export function packKindVerdict(kind: PackKind): PackKindVerdict {
  return FAIL_CLOSED.has(kind) ? "fail_closed" : "upload_ok";
}

export function packKindHonesty(kind: PackKind): string {
  switch (kind) {
    case "dwg":
      return "Closed .dwg ingest is fail-closed on MVP. Same mark as vector PDF or DXF. Not a silent skip.";
    case "rvt":
      return "Native RVT is not an ingest product. Export IFC from the authoring tool. Fail-closed.";
    case "nwd":
      return "Native NWD is not an ingest product. Ask the appointing party for a federation IFC. Stock Navisworks does not write IFC.";
    case "lir":
      return "Native .lir is not parsed. Upload a readable calculation note (PDF/Excel).";
    case "zip":
      return "ZIP is inspected on the server. Autodesk natives inside stay fail-closed.";
    case "ids":
      return "IDS 1.0 rule set. A requested set that cannot load fails closed.";
    case "ifc":
      return "IFC is the shared-gate model format.";
    case "pdf":
      return "PDF/A and vector PDF are the drawing/note exchange.";
    case "office":
      return "Office files compare declared fields; MATCH is not calculation correctness.";
    case "dxf":
      return "DXF is optional ingest, not a closed .dwg reader.";
    default:
      return "Unknown type. The server validates magic bytes. Do not assume success from a 200 on another file.";
  }
}
