import { useEffect, useRef } from "react";
import { UI_COPY } from "../../lib/ui-copy";
import "../../styles/export-unsaved-dialog.css";

export type ExportUnsavedDialogProps = {
  /** Подпись формата, по которому задан вопрос: подтверждается ровно он. */
  formatLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
};

/**
 * FE-CRUFT-02: предупреждение о несохранённом черновике перед выгрузкой.
 *
 * Раньше здесь работало нативное `confirm`. Браузер добавлял к тексту
 * служебную строку с адресом стенда, окно нельзя было озаглавить, оформить
 * и проверить доступность, а поток кода блокировался синхронно.
 *
 * Теперь вопрос задаёт сама оболочка. Механика повторяет диалог
 * несохранённого черновика, чтобы в продукте было одно поведение
 * подтверждений:
 * - `dialog.showModal()` — верхний слой и собственная изоляция фокуса;
 * - `role="alertdialog"` + `aria-labelledby` / `aria-describedby` — заголовок
 *   и предупреждение объявляются целиком, а не как безымянное окно;
 * - первой в порядке обхода стоит безопасная кнопка «вернуться к правке»:
 *   случайный повторный ввод не выгружает файл;
 * - обход по Tab замкнут внутри диалога, клавиша выхода равна отказу;
 * - события клавиатуры не всплывают, поэтому горячие клавиши триажа не
 *   срабатывают за спиной у диалога.
 *
 * Текст предупреждения берётся из `UI_COPY.exportUnsavedConfirm` — того же
 * ключа, который дословно сверяет репетиционный смоук (FE-DRIFT-01).
 */
export default function ExportUnsavedDialog({
  formatLabel,
  onConfirm,
  onCancel,
}: ExportUnsavedDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    dialog.showModal();
    cancelRef.current?.focus();
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
      className="keyboard-help-dialog export-unsaved-dialog"
      role="alertdialog"
      aria-modal="true"
      tabIndex={-1}
      aria-labelledby="export-unsaved-title"
      aria-describedby="export-unsaved-message"
      data-testid="export-unsaved-dialog"
      onCancel={(event) => {
        event.preventDefault();
        onCancel();
      }}
      onKeyDown={(event) => {
        event.stopPropagation();
        if (event.key !== "Tab" || event.ctrlKey || event.altKey || event.metaKey) {
          return;
        }
        const buttons = Array.from(
          event.currentTarget.querySelectorAll<HTMLButtonElement>("button:not(:disabled)"),
        );
        const first = buttons[0];
        const last = buttons[buttons.length - 1];
        if (!first || !last) {
          return;
        }
        const active = document.activeElement;
        if (event.shiftKey && (active === first || active === event.currentTarget)) {
          event.preventDefault();
          last.focus();
          return;
        }
        if (!event.shiftKey && active === last) {
          event.preventDefault();
          first.focus();
        }
      }}
    >
      <h2 id="export-unsaved-title">{UI_COPY.exportUnsavedTitle}</h2>
      <p id="export-unsaved-message" data-testid="export-unsaved-message">
        {UI_COPY.exportUnsavedConfirm}
      </p>
      <p className="compact-copy export-unsaved-format" data-testid="export-unsaved-format">
        {UI_COPY.exportUnsavedFormat(formatLabel)}
      </p>
      <div className="export-unsaved-actions">
        <button
          ref={cancelRef}
          type="button"
          className="toolbar-button export-unsaved-cancel"
          data-testid="export-unsaved-cancel"
          onClick={onCancel}
        >
          {UI_COPY.exportUnsavedCancel}
        </button>
        <button
          type="button"
          className="toolbar-button toolbar-button-primary export-unsaved-continue"
          data-testid="export-unsaved-continue"
          onClick={onConfirm}
        >
          {UI_COPY.exportUnsavedContinue}
        </button>
      </div>
    </dialog>
  );
}
