/**
 * Плотность рабочего места эксперта.
 *
 * Модуль намеренно не знает про DOM и localStorage напрямую: он принимает
 * структурные цели (`dataset`) и хранилище, поэтому проверяется без jsdom и
 * не падает там, где браузер запрещает доступ к хранилищу.
 *
 * Значение попадает в атрибут `data-density` на корневом элементе, а слой
 * `styles/visual-language/10-ergonomics.css` включает по нему компактный шаг.
 * Обычная плотность остаётся исходной: включение переключателя не меняет
 * ни одного правила по умолчанию.
 */

export const DENSITY_MODES = ["comfortable", "compact"] as const;

export type DensityMode = (typeof DENSITY_MODES)[number];

/** Ключ хранилища; префикс продукта отделяет настройку от чужих ключей. */
export const DENSITY_STORAGE_KEY = "aerobim.ui.density";

/** Имя data-атрибута в camelCase, как его видит `dataset`. */
export const DENSITY_DATASET_KEY = "density";

export const DEFAULT_DENSITY: DensityMode = "comfortable";

/** Минимальная структурная цель: подходит и HTMLElement, и заглушке в тесте. */
export type DensityTarget = { dataset: Record<string, string | undefined> };

/** Минимальный контракт хранилища: подходит и localStorage, и заглушке. */
export type DensityStore = {
  getItem: (key: string) => string | null;
  setItem: (key: string, value: string) => void;
};

export function normalizeDensity(value: unknown): DensityMode {
  return DENSITY_MODES.includes(value as DensityMode) ? (value as DensityMode) : DEFAULT_DENSITY;
}

export function nextDensity(mode: DensityMode): DensityMode {
  return mode === "compact" ? "comfortable" : "compact";
}

export function applyDensity(
  target: DensityTarget | null | undefined,
  mode: DensityMode | string | null | undefined,
): DensityMode {
  const normalized = normalizeDensity(mode);
  if (target) {
    target.dataset[DENSITY_DATASET_KEY] = normalized;
  }
  return normalized;
}

export function readStoredDensity(store: DensityStore | null | undefined): DensityMode {
  if (!store) {
    return DEFAULT_DENSITY;
  }
  try {
    return normalizeDensity(store.getItem(DENSITY_STORAGE_KEY));
  } catch {
    return DEFAULT_DENSITY;
  }
}

/** Запись настройки не должна ронять интерфейс: квоты и приватный режим. */
export function persistDensity(
  store: DensityStore | null | undefined,
  mode: DensityMode | string | null | undefined,
): DensityMode {
  const normalized = normalizeDensity(mode);
  if (store) {
    try {
      store.setItem(DENSITY_STORAGE_KEY, normalized);
    } catch {
      /* настройка остаётся в памяти сессии */
    }
  }
  return normalized;
}

export function initDensity(
  target: DensityTarget | null | undefined,
  store: DensityStore | null | undefined,
): DensityMode {
  return applyDensity(target, readStoredDensity(store));
}

export function documentDensityTarget(): DensityTarget | null {
  return typeof document === "undefined" ? null : document.documentElement;
}

export function browserDensityStore(): DensityStore | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}
