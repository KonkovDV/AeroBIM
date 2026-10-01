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

export type PackDocumentRole =
  | "ifc"
  | "ids"
  | "drawing"
  | "requirement"
  | "technical_spec"
  | "calculation";

export type PackDraftSlot = Exclude<PackDocumentRole, "drawing">;

export type PackDraftApplyNote =
  | { kind: "filled"; slot: PackDocumentRole }
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

function slotLabel(slot: PackDocumentRole): string {
  switch (slot) {
    case "ifc":
      return "IFC";
    case "ids":
      return "IDS";
    case "drawing":
      return "чертёж";
    case "requirement":
      return "ТЗ";
    case "technical_spec":
      return "спецификация";
    case "calculation":
      return "расчётная записка";
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

function looksLike(filename: string, needles: readonly string[]): boolean {
  const tokens = filename
    .toLowerCase()
    .split(/[^a-zа-яё0-9]+/)
    .filter(Boolean);
  return needles.some(
    (needle) => tokens.includes(needle) || tokens.some((token) => token.startsWith(needle)),
  );
}

/** Filename is a hint, not a proven document class. */
export function inferDocumentRole(filename: string): PackDocumentRole | "unsupported" {
  const kind = detectPackKind(filename);
  if (kind === "ifc") {
    return "ifc";
  }
  if (kind === "ids") {
    return "ids";
  }
  if (kind === "pdf") {
    if (looksLike(filename, ["tz", "тз", "итз", "eir", "brief", "треб"])) {
      return "requirement";
    }
    if (looksLike(filename, ["lira", "лира", "calc", "расч", "смет", "арматур"])) {
      return "calculation";
    }
    if (looksLike(filename, ["spec", "специф"])) {
      return "technical_spec";
    }
    return "drawing";
  }
  if (kind === "office") {
    const lower = filename.toLowerCase();
    if (lower.endsWith(".xlsx") || lower.endsWith(".xlsm")) {
      return "calculation";
    }
    if (looksLike(filename, ["spec", "специф"])) {
      return "technical_spec";
    }
    return "requirement";
  }
  return "unsupported";
}

export function roleAcceptsFilename(role: PackDocumentRole, filename: string): boolean {
  const kind = detectPackKind(filename);
  if (role === "ifc") {
    return kind === "ifc";
  }
  if (role === "ids") {
    return kind === "ids";
  }
  if (role === "drawing" || role === "requirement" || role === "technical_spec" || role === "calculation") {
    return kind === "pdf" || kind === "office";
  }
  return false;
}

function withoutPath(draft: PackDraft, path: string): PackDraft {
  return {
    ifcPath: draft.ifcPath === path ? null : draft.ifcPath,
    idsPath: draft.idsPath === path ? null : draft.idsPath,
    requirementPath: draft.requirementPath === path ? null : draft.requirementPath,
    technicalSpecPath: draft.technicalSpecPath === path ? null : draft.technicalSpecPath,
    calculationPath: draft.calculationPath === path ? null : draft.calculationPath,
    drawings: draft.drawings.filter((row) => row.path !== path),
  };
}

function placeRole(
  draft: PackDraft,
  path: string,
  filename: string,
  role: PackDocumentRole,
): PackDraftApplyResult {
  const cleaned = withoutPath(draft, path);
  switch (role) {
    case "ifc":
      return { draft: { ...cleaned, ifcPath: path }, note: slotNote("ifc", cleaned.ifcPath) };
    case "ids":
      return { draft: { ...cleaned, idsPath: path }, note: slotNote("ids", cleaned.idsPath) };
    case "requirement":
      return {
        draft: { ...cleaned, requirementPath: path },
        note: slotNote("requirement", cleaned.requirementPath),
      };
    case "technical_spec":
      return {
        draft: { ...cleaned, technicalSpecPath: path },
        note: slotNote("technical_spec", cleaned.technicalSpecPath),
      };
    case "calculation":
      return {
        draft: { ...cleaned, calculationPath: path },
        note: slotNote("calculation", cleaned.calculationPath),
      };
    case "drawing":
      return {
        draft: {
          ...cleaned,
          drawings: [...cleaned.drawings, { path, filename }],
        },
        note: { kind: "drawing_added" },
      };
  }
}

export function applyUploadedFileResult(
  draft: PackDraft,
  path: string,
  filename: string,
  role?: PackDocumentRole,
): PackDraftApplyResult {
  const resolved = role ?? inferDocumentRole(filename);
  if (resolved === "unsupported") {
    return { draft, note: { kind: "not_in_draft", packKind: detectPackKind(filename) } };
  }
  if (role && !roleAcceptsFilename(role, filename)) {
    return { draft, note: { kind: "not_in_draft", packKind: detectPackKind(filename) } };
  }
  return placeRole(draft, path, filename, resolved);
}

export function reassignPackDraftRole(
  draft: PackDraft,
  path: string,
  filename: string,
  role: PackDocumentRole,
): PackDraftApplyResult {
  return applyUploadedFileResult(draft, path, filename, role);
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

/** Однострочный состав пакета для экранов загрузки и прогона. Не «пакет обработан». */
export function packCompositionLine(draft: PackDraft): string {
  const parts = [
    `IFC ${draft.ifcPath ? "✓" : "—"}`,
    `IDS ${draft.idsPath ? "✓" : "—"}`,
    `листы ${draft.drawings.length}`,
    `ТЗ ${draft.requirementPath ? "✓" : "—"}`,
    `спец. ${draft.technicalSpecPath ? "✓" : "—"}`,
    `расчёт ${draft.calculationPath ? "✓" : "—"}`,
  ];
  return parts.join(" · ");
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
