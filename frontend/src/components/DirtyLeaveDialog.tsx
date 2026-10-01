import { useEffect, useRef } from "react";
import { UI_COPY } from "../lib/ui-copy";
import "../styles/dirty-leave-dialog.css";

type DirtyLeaveDialogProps = {
  onSave: () => void;
  onDiscard: () => void;
  onStay: () => void;
  busy?: boolean;
  saveDisabled?: boolean;
  errorMessage?: string | null;
};

export default function DirtyLeaveDialog({
  onSave, onDiscard, onStay, busy = false, saveDisabled = false, errorMessage = null,
}: DirtyLeaveDialogProps) {
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

  useEffect(() => {
    (busy ? dialogRef.current : stayRef.current)?.focus();
  }, [busy]);

  return (
    <dialog
      ref={dialogRef}
      className="keyboard-help-dialog dirty-leave-dialog"
      aria-modal="true"
      tabIndex={-1}
      aria-labelledby="dirty-leave-title"
      aria-describedby="dirty-leave-description"
      data-testid="dirty-leave-dialog"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onStay();
      }}
      onKeyDown={(event) => {
        event.stopPropagation();
        if (event.key !== "Tab" || event.ctrlKey || event.altKey || event.metaKey) return;
        const buttons = event.currentTarget.querySelectorAll<HTMLButtonElement>("button:not(:disabled)");
        const first = buttons[0];
        const last = buttons[buttons.length - 1];
        if (!first || (!event.shiftKey && document.activeElement === last) ||
            (event.shiftKey && document.activeElement === first)) {
          event.preventDefault();
          (event.shiftKey ? last : first)?.focus();
        }
      }}
    >
      <h2 id="dirty-leave-title">{UI_COPY.dirtyLeaveTitle}</h2>
      <p id="dirty-leave-description">{UI_COPY.dirtyLeaveBody}</p>
      <p className="dirty-leave-status" role="status">{busy ? UI_COPY.savingRemark : ""}</p>
      {errorMessage ? <p className="dirty-leave-error" role="alert">{errorMessage}</p> : null}
      <div className="dirty-leave-actions" aria-busy={busy}>
        <button type="button" className="toolbar-button dirty-leave-save" disabled={busy || saveDisabled} onClick={onSave}>
          {UI_COPY.dirtyLeaveSave}
        </button>
        <button type="button" className="toolbar-button dirty-leave-discard" disabled={busy} onClick={onDiscard}>
          {UI_COPY.dirtyLeaveDiscard}
        </button>
        <button ref={stayRef} type="button" className="toolbar-button" disabled={busy} onClick={onStay}>
          {UI_COPY.dirtyLeaveStay}
        </button>
      </div>
    </dialog>
  );
}
