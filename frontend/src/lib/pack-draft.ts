/** Draft of a pack assembled from successive uploads. Not a customer-pack claim. */

import { detectPackKind, type PackKind } from "./pack-kind";

export type PackDrawing = { path: string; filename: string };

export type PackDraft = {
  ifcPath: string | null;
  idsPath: string | null;
  drawings: PackDrawing[];
  requirementPath: string | null;
  technicalSpecPath: string | null;
  calculationPath: string | null;
};

export const EMPTY_PACK_DRAFT: PackDraft = {
  ifcPath: null,
  idsPath: null,
  drawings: [],
  requirementPath: null,
  technicalSpecPath: null,
  calculationPath: null,
};

export type AnalyzeSubmitBody = {
  ifc_path?: string;
  ids_path?: string;
  requirement_path?: string;
  technical_spec_path?: string;
  calculation_path?: string;
  drawings?: Array<{ path: string }>;
};

export type PackDraftSlot = "ifc" | "ids" | "requirement" | "calculation";

export type PackDraftApplyNote =
  | { kind: "filled"; slot: PackDraftSlot }
  | { kind: "replaced"; slot: PackDraftSlot; previousPath: string }
  | { kind: "drawing_added" }
  | { kind: "not_in_draft"; packKind: PackKind };

export type PackDraftApplyResult = {
  draft: PackDraft;
  note: PackDraftApplyNote;
};

function slotNote(slot: PackDraftSlot, previous: string | null): PackDraftApplyNote {
  if (previous) {
    return { kind: "replaced", slot, previousPath: previous };
  }
  return { kind: "filled", slot };
}

function slotLabel(slot: PackDraftSlot): string {
  switch (slot) {
    case "ifc":
      return "IFC";
    case "ids":
      return "IDS";
    case "requirement":
      return "ТЗ/офис";
    case "calculation":
      return "смета/xlsx";
  }
}

/** HD14-FE-01: replacement and not-in-draft must be visible, not a silent slot overwrite. */
export function describePackDraftApplyNote(note: PackDraftApplyNote): string {
  switch (note.kind) {
    case "replaced":
      return `Слот ${slotLabel(note.slot)} заменён (было ${note.previousPath}). Это не «ещё один файл в комплекте».`;
    case "filled":
      return `Слот ${slotLabel(note.slot)} заполнен.`;
    case "drawing_added":
      return "Лист добавлен в список чертежей (не одноместный слот).";
    case "not_in_draft":
      return `Файл на сервере, в draft комплекта не попал (${note.packKind}). Прогон его не увидит.`;
  }
}

export function applyUploadedFileResult(
  draft: PackDraft,
  path: string,
  filename: string,
): PackDraftApplyResult {
  const kind = detectPackKind(filename);
  switch (kind) {
    case "ifc":
      return { draft: { ...draft, ifcPath: path }, note: slotNote("ifc", draft.ifcPath) };
    case "ids":
      return { draft: { ...draft, idsPath: path }, note: slotNote("ids", draft.idsPath) };
    case "pdf":
      return {
        draft: {
          ...draft,
          drawings: [...draft.drawings.filter((row) => row.path !== path), { path, filename }],
        },
        note: { kind: "drawing_added" },
      };
    case "office": {
      const lower = filename.toLowerCase();
      if (lower.endsWith(".xlsx") || lower.endsWith(".xlsm")) {
        return {
          draft: { ...draft, calculationPath: path },
          note: slotNote("calculation", draft.calculationPath),
        };
      }
      return {
        draft: { ...draft, requirementPath: path },
        note: slotNote("requirement", draft.requirementPath),
      };
    }
    default:
      return { draft, note: { kind: "not_in_draft", packKind: kind } };
  }
}

export function applyUploadedFile(draft: PackDraft, path: string, filename: string): PackDraft {
  return applyUploadedFileResult(draft, path, filename).draft;
}

export function packDraftHasAny(draft: PackDraft): boolean {
  return Boolean(
    draft.ifcPath ||
      draft.idsPath ||
      draft.drawings.length > 0 ||
      draft.requirementPath ||
      draft.technicalSpecPath ||
      draft.calculationPath,
  );
}

export function toAnalyzeSubmitBody(draft: PackDraft): AnalyzeSubmitBody {
  const body: AnalyzeSubmitBody = {};
  if (draft.ifcPath) {
    body.ifc_path = draft.ifcPath;
  }
  if (draft.idsPath) {
    body.ids_path = draft.idsPath;
  }
  if (draft.requirementPath) {
    body.requirement_path = draft.requirementPath;
  }
  if (draft.technicalSpecPath) {
    body.technical_spec_path = draft.technicalSpecPath;
  }
  if (draft.calculationPath) {
    body.calculation_path = draft.calculationPath;
  }
  if (draft.drawings.length > 0) {
    body.drawings = draft.drawings.map((row) => ({ path: row.path }));
  }
  return body;
}

export function packDraftFromIfc(ifcPath: string | null): PackDraft {
  return { ...EMPTY_PACK_DRAFT, ifcPath };
}
