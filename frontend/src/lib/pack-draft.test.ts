import { describe, expect, it } from "vitest";
import {
  applyUploadedFile,
  applyUploadedFileResult,
  describePackDraftApplyNote,
  EMPTY_PACK_DRAFT,
  packCompositionLine,
  packDraftHasAny,
  reassignPackDraftRole,
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

  it("renders the pack composition line without claiming a processed pack", () => {
    expect(packCompositionLine(EMPTY_PACK_DRAFT)).toBe(
      "IFC — · IDS — · листы 0 · ТЗ — · спец. — · расчёт —",
    );
    let draft = applyUploadedFile(EMPTY_PACK_DRAFT, "models/walls.ifc", "walls.ifc");
    draft = applyUploadedFile(draft, "sheets/a101.pdf", "A-101.pdf");
    draft = applyUploadedFile(draft, "sheets/a102.pdf", "A-102.pdf");
    expect(packCompositionLine(draft)).toBe("IFC ✓ · IDS — · листы 2 · ТЗ — · спец. — · расчёт —");
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

  it("does not treat a waltz PDF as a TZ requirement", () => {
    const { draft } = applyUploadedFileResult(EMPTY_PACK_DRAFT, "sheets/waltz.pdf", "waltz.pdf");
    expect(draft.requirementPath).toBeNull();
    expect(draft.drawings).toEqual([{ path: "sheets/waltz.pdf", filename: "waltz.pdf" }]);
  });

  it("hints PDF role from the filename and lets the operator reassign it", () => {
    const tz = applyUploadedFileResult(EMPTY_PACK_DRAFT, "docs/tz.pdf", "TZ-01.pdf");
    expect(tz.draft.requirementPath).toBe("docs/tz.pdf");
    expect(tz.draft.drawings).toEqual([]);
    const lira = applyUploadedFileResult(tz.draft, "calc/note.pdf", "lira-arm.pdf");
    expect(lira.draft.calculationPath).toBe("calc/note.pdf");
    const spec = applyUploadedFileResult(lira.draft, "spec/q.docx", "specification.docx");
    expect(spec.draft.technicalSpecPath).toBe("spec/q.docx");
    const reassigned = reassignPackDraftRole(spec.draft, "docs/tz.pdf", "TZ-01.pdf", "drawing");
    expect(reassigned.draft.requirementPath).toBeNull();
    expect(reassigned.draft.drawings).toEqual([{ path: "docs/tz.pdf", filename: "TZ-01.pdf" }]);
    expect(toAnalyzeSubmitBody(reassigned.draft)).toMatchObject({
      calculation_path: "calc/note.pdf",
      technical_spec_path: "spec/q.docx",
      drawings: [{ path: "docs/tz.pdf" }],
    });
  });
});
