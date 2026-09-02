import { describe, expect, it } from "vitest";
import {
  applyUploadedFile,
  applyUploadedFileResult,
  describePackDraftApplyNote,
  EMPTY_PACK_DRAFT,
  packDraftHasAny,
  toAnalyzeSubmitBody,
} from "./pack-draft";

describe("pack-draft", () => {
  it("routes IFC, IDS, PDF and Office into analyze fields without claiming a customer pack", () => {
    let draft = applyUploadedFile(EMPTY_PACK_DRAFT, "models/walls.ifc", "walls.ifc");
    draft = applyUploadedFile(draft, "rules/fire.ids", "fire.ids");
    draft = applyUploadedFile(draft, "sheets/a101.pdf", "A-101.pdf");
    draft = applyUploadedFile(draft, "calc/lira.xlsx", "lira.xlsx");
    draft = applyUploadedFile(draft, "tz/brief.docx", "brief.docx");
    expect(packDraftHasAny(draft)).toBe(true);
    expect(toAnalyzeSubmitBody(draft)).toEqual({
      ifc_path: "models/walls.ifc",
      ids_path: "rules/fire.ids",
      requirement_path: "tz/brief.docx",
      calculation_path: "calc/lira.xlsx",
      drawings: [{ path: "sheets/a101.pdf" }],
    });
  });

  it("does not put fail-closed natives into the analyze body", () => {
    const draft = applyUploadedFile(EMPTY_PACK_DRAFT, "closed/tower.rvt", "tower.rvt");
    expect(toAnalyzeSubmitBody(draft)).toEqual({});
    expect(packDraftHasAny(draft)).toBe(false);
  });

  it("routes .ifczip into the IFC slot", () => {
    const { draft, note } = applyUploadedFileResult(EMPTY_PACK_DRAFT, "models/a.ifczip", "a.ifczip");
    expect(draft.ifcPath).toBe("models/a.ifczip");
    expect(note).toEqual({ kind: "filled", slot: "ifc" });
  });

  it("reports a slot replacement instead of a silent overwrite", () => {
    const first = applyUploadedFile(EMPTY_PACK_DRAFT, "models/a.ifc", "a.ifc");
    const { draft, note } = applyUploadedFileResult(first, "models/b.ifc", "b.ifc");
    expect(draft.ifcPath).toBe("models/b.ifc");
    expect(note).toEqual({ kind: "replaced", slot: "ifc", previousPath: "models/a.ifc" });
    expect(describePackDraftApplyNote(note)).toMatch(/заменён/);
  });

  it("says uploaded-but-not-in-draft for zip and other kinds", () => {
    const { draft, note } = applyUploadedFileResult(EMPTY_PACK_DRAFT, "bundle.zip", "bundle.zip");
    expect(draft).toEqual(EMPTY_PACK_DRAFT);
    expect(note).toEqual({ kind: "not_in_draft", packKind: "zip" });
    expect(describePackDraftApplyNote(note)).toMatch(/не попал/);
  });
});
