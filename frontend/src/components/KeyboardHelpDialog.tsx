import { useEffect, useRef } from "react";
import { UI_COPY } from "../lib/ui-copy";

type Props = {
  onClose: () => void;
  shortcutsEnabled: boolean;
  onShortcutsChange: (enabled: boolean) => void;
};

const COMMANDS = [
  ["J / ↓", UI_COPY.keyboardHelpNext],
  ["K / ↑", UI_COPY.keyboardHelpPrev],
  ["PageDown", UI_COPY.keyboardHelpPageDown],
  ["PageUp", UI_COPY.keyboardHelpPageUp],
  ["Home", UI_COPY.keyboardHelpHome],
  ["End", UI_COPY.keyboardHelpEnd],
  ["E", UI_COPY.keyboardHelpEdit],
  ["A", UI_COPY.keyboardHelpAccept],
  ["R", UI_COPY.keyboardHelpReject],
  ["Ctrl / Cmd + Enter", UI_COPY.keyboardHelpSave],
  ["?", UI_COPY.keyboardHelpOpen],
  ["Esc", UI_COPY.keyboardHelpEsc],
] as const;

/** Native modal: focus containment, inert background and focus return, without a dependency. */
export default function KeyboardHelpDialog({ onClose, shortcutsEnabled, onShortcutsChange }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    dialog.showModal();
    closeRef.current?.focus();
    document.body.style.overflow = "hidden";
    return () => {
      dialog.close();
      document.body.style.overflow = previousOverflow;
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) previousFocus.focus();
    };
  }, []);

  return (
    <dialog
      ref={dialogRef}
      className="keyboard-help-dialog"
      aria-modal="true"
      aria-labelledby="keyboard-help-title"
      aria-describedby="keyboard-help-description"
      onCancel={(event) => { event.preventDefault(); onClose(); }}
      onKeyDown={(event) => {
        event.stopPropagation();
        if (event.key !== "Tab") return;
        const controls = event.currentTarget.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
        );
        const first = controls[0];
        const last = controls[controls.length - 1];
        if ((!event.shiftKey && document.activeElement === last) ||
            (event.shiftKey && document.activeElement === first)) {
          event.preventDefault();
          (event.shiftKey ? last : first)?.focus();
        }
      }}
    >
      <header className="keyboard-help-heading">
        <h2 id="keyboard-help-title">{UI_COPY.keyboardHelpAria}</h2>
        <button ref={closeRef} type="button" className="toolbar-button" onClick={onClose}>
          {UI_COPY.keyboardHelpClose}
        </button>
      </header>
      <p id="keyboard-help-description">
        {UI_COPY.keyboardHelpIntro}
      </p>
      <dl className="keyboard-help-commands">
        {COMMANDS.map(([keys, description]) => (
          <div key={keys}><dt><kbd>{keys}</kbd></dt><dd>{description}</dd></div>
        ))}
      </dl>
      <label className="keyboard-help-preference">
        <input type="checkbox" checked={shortcutsEnabled}
          onChange={(event) => onShortcutsChange(event.target.checked)} />
        {UI_COPY.keyboardHelpEnable}
      </label>
      <p className="keyboard-help-note">
        {UI_COPY.keyboardHelpNote}
      </p>
    </dialog>
  );
}
