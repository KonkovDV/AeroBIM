import { useRef, useState } from "react";
import {
  applyUploadedFileResult,
  describePackDraftApplyNote,
  EMPTY_PACK_DRAFT,
  type PackDraftApplyNote,
} from "../lib/pack-draft";

export function usePackDraft() {
  const [packDraft, setPackDraft] = useState(EMPTY_PACK_DRAFT);
  const packDraftRef = useRef(packDraft);
  packDraftRef.current = packDraft;
  const [draftApplyNote, setDraftApplyNote] = useState<string | null>(null);

  function applyUpload(path: string, filename: string): PackDraftApplyNote {
    const { draft, note } = applyUploadedFileResult(packDraftRef.current, path, filename);
    packDraftRef.current = draft;
    setPackDraft(draft);
    if (note.kind === "replaced" || note.kind === "not_in_draft") {
      setDraftApplyNote(describePackDraftApplyNote(note));
    } else {
      setDraftApplyNote(null);
    }
    return note;
  }

  return { packDraft, draftApplyNote, applyUpload };
}
