import { useEffect, useRef } from "react";
import { UI_COPY } from "../lib/ui-copy";

type Props = {
  onClose: () => void;
  shortcutsEnabled: boolean;
  onShortcutsChange: (enabled: boolean) => void;
};

const COMMANDS = [
  ["J / ↓", "Следующая находка"],
  ["K / ↑", "Предыдущая находка"],
  ["E", "Перейти к тексту замечания"],
  ["A", "Подтвердить замечание"],
  ["R", "Отклонить замечание"],
  ["Ctrl / Cmd + Enter", "Сохранить текст из редактора"],
  ["?", "Открыть справку"],
  ["Esc", "Закрыть справку"],
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
          Закрыть
        </button>
      </header>
      <p id="keyboard-help-description">
        Проверяйте доказательства, затем принимайте решение. Команды подтверждения и отклонения
        доступны только при разрешённых правах эксперта.
      </p>
      <dl className="keyboard-help-commands">
        {COMMANDS.map(([keys, description]) => (
          <div key={keys}><dt><kbd>{keys}</kbd></dt><dd>{description}</dd></div>
        ))}
      </dl>
      <label className="keyboard-help-preference">
        <input type="checkbox" checked={shortcutsEnabled}
          onChange={(event) => onShortcutsChange(event.target.checked)} />
        Быстрые клавиши триажа
      </label>
      <p className="keyboard-help-note">
        Отключите их при голосовом вводе или диктовке. Кнопки, переходы по Tab и сохранение
        из редактора остаются доступны. В справке клавиши не подтверждают и не отклоняют замечания.
      </p>
    </dialog>
  );
}
