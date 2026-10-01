import { useRef, useState } from "react";
import { detectPackKind } from "../lib/pack-kind";
import {
  applyUploadedFileResult,
  describePackDraftApplyNote,
  EMPTY_PACK_DRAFT,
  inferDocumentRole,
  reassignPackDraftRole,
  type PackDocumentRole,
  type PackDraftApplyNote,
} from "../lib/pack-draft";

export type PackRoleChoice = {
  path: string;
  filename: string;
  role: PackDocumentRole;
};

export function usePackDraft() {
  const [packDraft, setPackDraft] = useState(EMPTY_PACK_DRAFT);
  const packDraftRef = useRef(packDraft);
  packDraftRef.current = packDraft;
  const [draftApplyNote, setDraftApplyNote] = useState<string | null>(null);
  const [pendingRole, setPendingRole] = useState<PackRoleChoice | null>(null);

  function rememberNote(note: PackDraftApplyNote): void {
    if (note.kind === "replaced" || note.kind === "not_in_draft") {
      setDraftApplyNote(describePackDraftApplyNote(note));
    } else {
      setDraftApplyNote(null);
    }
  }

  function applyUpload(path: string, filename: string): PackDraftApplyNote {
    const { draft, note } = applyUploadedFileResult(packDraftRef.current, path, filename);
    packDraftRef.current = draft;
    setPackDraft(draft);
    rememberNote(note);
    const kind = detectPackKind(filename);
    const inferred = inferDocumentRole(filename);
    if ((kind === "pdf" || kind === "office") && inferred !== "unsupported") {
      setPendingRole({ path, filename, role: inferred });
    } else {
      setPendingRole(null);
    }
    return note;
  }

  function chooseRole(role: PackDocumentRole): void {
    if (!pendingRole) {
      return;
    }
    const { draft, note } = reassignPackDraftRole(
      packDraftRef.current,
      pendingRole.path,
      pendingRole.filename,
      role,
    );
    packDraftRef.current = draft;
    setPackDraft(draft);
    rememberNote(note);
    setPendingRole({ ...pendingRole, role });
  }

  return { packDraft, draftApplyNote, pendingRole, applyUpload, chooseRole };
}
