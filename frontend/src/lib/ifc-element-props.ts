/** Разбор строк web-ifc: имя/тип/этаж. Не QTO и не замер для сметы. */

export type IfcElementProps = {
  guid: string;
  expressId: number;
  typeName: string;
  name: string | null;
  storeyName: string | null;
};

export type IfcStoreyOption = {
  expressId: number;
  name: string | null;
  guid: string | null;
};

export function unwrapScalar(raw: unknown): unknown {
  if (raw === null || raw === undefined) {
    return null;
  }
  if (typeof raw === "object" && "value" in (raw as object)) {
    return (raw as { value: unknown }).value;
  }
  return raw;
}

export function unwrapString(raw: unknown): string | null {
  const value = unwrapScalar(raw);
  if (typeof value !== "string") {
    return null;
  }
  const text = value.trim();
  return text.length > 0 ? text : null;
}

export function unwrapExpressId(raw: unknown): number | null {
  if (typeof raw === "number" && Number.isInteger(raw) && raw >= 0) {
    return raw;
  }
  if (raw && typeof raw === "object") {
    const record = raw as { value?: unknown; expressID?: unknown };
    if (typeof record.expressID === "number") {
      return record.expressID;
    }
    if (typeof record.value === "number") {
      return record.value;
    }
  }
  return null;
}

export function iterateIdVector(vector: unknown): number[] {
  if (!vector) {
    return [];
  }
  if (Array.isArray(vector)) {
    return vector
      .map((item) => unwrapExpressId(item))
      .filter((id): id is number => id !== null);
  }
  const sized = vector as { size?: () => number; get?: (index: number) => unknown };
  if (typeof sized.size === "function" && typeof sized.get === "function") {
    const out: number[] = [];
    const count = sized.size();
    for (let index = 0; index < count; index += 1) {
      const id = unwrapExpressId(sized.get(index));
      if (id !== null) {
        out.push(id);
      }
    }
    return out;
  }
  const single = unwrapExpressId(vector);
  return single === null ? [] : [single];
}

export function unwrapExpressIdList(raw: unknown): number[] {
  const nested = unwrapScalar(raw);
  return iterateIdVector(nested ?? raw);
}

export type SpatialRelationLine = {
  RelatingStructure?: unknown;
  RelatedElements?: unknown;
};

export function indexContainedInStorey(
  relations: SpatialRelationLine[],
  storeyIds: ReadonlySet<number>,
): Map<number, number> {
  const elementToStorey = new Map<number, number>();
  for (const relation of relations) {
    const storeyId = unwrapExpressId(relation.RelatingStructure);
    if (storeyId === null || !storeyIds.has(storeyId)) {
      continue;
    }
    for (const elementId of unwrapExpressIdList(relation.RelatedElements)) {
      elementToStorey.set(elementId, storeyId);
    }
  }
  return elementToStorey;
}
