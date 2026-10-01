/** Удобство ввода, не разрешение на действия: права всегда проверяет сервер. */
const STORAGE_KEY = "aerobim-triage-shortcuts-v1";

export function readTriageShortcuts(): boolean {
  try {
    return typeof window === "undefined" || window.localStorage.getItem(STORAGE_KEY) !== "off";
  } catch {
    return true;
  }
}

export function persistTriageShortcuts(enabled: boolean): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, enabled ? "on" : "off");
  } catch {
    // Запрет хранилища не должен ломать рабочее место; выбор живёт в state.
  }
}
