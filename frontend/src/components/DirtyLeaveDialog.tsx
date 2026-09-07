import { useEffect, useRef } from "react";
import { UI_COPY } from "../lib/ui-copy";

type DirtyLeaveDialogProps = {
  onSave: () => void;
  onDiscard: () => void;
  onStay: () => void;
};

export default function DirtyLeaveDialog({ onSave, onDiscard, onStay }: DirtyLeaveDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const stayRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    dialog.showModal();
    stayRef.current?.focus();
    document.body.style.overflow = "hidden";
    return () => {
      dialog.close();
      document.body.style.overflow = previousOverflow;
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) {
        previousFocus.focus();
      }
    };
  }, []);

  return (
    <dialog
      ref={dialogRef}
      className="keyboard-help-dialog"
      aria-modal="true"
      aria-labelledby="dirty-leave-title"
      data-testid="dirty-leave-dialog"
      onCancel={(event) => {
        event.preventDefault();
        onStay();
      }}
    >
      <h2 id="dirty-leave-title">{UI_COPY.dirtyLeaveTitle}</h2>
      <p>{UI_COPY.dirtyLeaveBody}</p>
      <div className="remark-actions">
        <button type="button" className="toolbar-button" onClick={onSave}>
          {UI_COPY.dirtyLeaveSave}
        </button>
        <button type="button" className="toolbar-button" onClick={onDiscard}>
          {UI_COPY.dirtyLeaveDiscard}
        </button>
        <button ref={stayRef} type="button" className="toolbar-button" onClick={onStay}>
          {UI_COPY.dirtyLeaveStay}
        </button>
      </div>
    </dialog>
  );
}
