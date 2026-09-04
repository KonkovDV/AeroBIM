/** Горизонтальные бары HITL by_type. Пустой журнал ≠ 0 % ошибок. */

export type KpiBarRow = {
  key: string;
  count: number;
  percent: number;
};

export type HitlDecisionSplit = {
  accepted: number;
  rejected: number;
};

/** Counts from review-kpi by_type. Not cycle days and not product accuracy. */
export function hitlDecisionSplit(
  byType: Record<string, number> | null | undefined,
): HitlDecisionSplit {
  return {
    accepted: typeof byType?.accepted === "number" ? byType.accepted : 0,
    rejected: typeof byType?.rejected === "number" ? byType.rejected : 0,
  };
}

export function kpiBarRows(byType: Record<string, number> | null | undefined): KpiBarRow[] {
  if (!byType) {
    return [];
  }
  const entries = Object.entries(byType).filter(([, count]) => typeof count === "number" && count > 0);
  const total = entries.reduce((sum, [, count]) => sum + count, 0);
  if (total === 0) {
    return [];
  }
  return entries
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([key, count]) => ({
      key,
      count,
      percent: Math.round((count / total) * 100),
    }));
}
