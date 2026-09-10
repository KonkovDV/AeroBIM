import { describe, expect, it } from "vitest";
import {
  DEFAULT_DENSITY,
  DENSITY_DATASET_KEY,
  DENSITY_MODES,
  DENSITY_STORAGE_KEY,
  applyDensity,
  initDensity,
  nextDensity,
  normalizeDensity,
  persistDensity,
  readStoredDensity,
  type DensityStore,
  type DensityTarget,
} from "./ui-density";

function target(): DensityTarget {
  return { dataset: {} };
}

function memoryStore(initial?: string): DensityStore & { values: Map<string, string> } {
  const values = new Map<string, string>();
  if (initial !== undefined) {
    values.set(DENSITY_STORAGE_KEY, initial);
  }
  return {
    values,
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => {
      values.set(key, value);
    },
  };
}

describe("плотность рабочего места", () => {
  it("знает две ступени и по умолчанию возвращает обычную", () => {
    expect([...DENSITY_MODES]).toEqual(["comfortable", "compact"]);
    expect(DEFAULT_DENSITY).toBe("comfortable");
    expect(normalizeDensity("compact")).toBe("compact");
    expect(normalizeDensity("COMPACT")).toBe("comfortable");
    expect(normalizeDensity(null)).toBe("comfortable");
    expect(normalizeDensity(undefined)).toBe("comfortable");
    expect(normalizeDensity({ mode: "compact" })).toBe("comfortable");
  });

  it("переключается туда и обратно без третьего состояния", () => {
    expect(nextDensity("comfortable")).toBe("compact");
    expect(nextDensity(nextDensity("comfortable"))).toBe("comfortable");
  });

  it("пишет режим в data-атрибут и терпит отсутствие цели", () => {
    const element = target();
    expect(applyDensity(element, "compact")).toBe("compact");
    expect(element.dataset[DENSITY_DATASET_KEY]).toBe("compact");
    expect(applyDensity(element, "мусор")).toBe("comfortable");
    expect(element.dataset[DENSITY_DATASET_KEY]).toBe("comfortable");
    expect(applyDensity(null, "compact")).toBe("compact");
  });

  it("читает сохранённый выбор и не верит чужому значению", () => {
    expect(readStoredDensity(memoryStore("compact"))).toBe("compact");
    expect(readStoredDensity(memoryStore("dense"))).toBe("comfortable");
    expect(readStoredDensity(memoryStore())).toBe("comfortable");
    expect(readStoredDensity(null)).toBe("comfortable");
  });

  it("переживает хранилище, которое бросает исключение", () => {
    const hostile: DensityStore = {
      getItem: () => {
        throw new Error("storage disabled");
      },
      setItem: () => {
        throw new Error("storage disabled");
      },
    };
    expect(readStoredDensity(hostile)).toBe("comfortable");
    expect(persistDensity(hostile, "compact")).toBe("compact");
  });

  it("сохраняет выбор и восстанавливает его при следующей загрузке", () => {
    const store = memoryStore();
    const element = target();
    expect(persistDensity(store, "compact")).toBe("compact");
    expect(store.values.get(DENSITY_STORAGE_KEY)).toBe("compact");
    expect(initDensity(element, store)).toBe("compact");
    expect(element.dataset[DENSITY_DATASET_KEY]).toBe("compact");
    expect(initDensity(target(), memoryStore())).toBe("comfortable");
  });
});
