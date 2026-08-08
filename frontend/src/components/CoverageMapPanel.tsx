import { useEffect, useMemo, useState } from "react";
import { fetchReportCoverage, type CheckCoverageMap } from "../lib/api";

const STATUS_CLASS: Record<string, string> = {
  no_findings: "cov-no-findings",
  findings: "cov-findings",
  not_checked: "cov-not-checked",
  insufficient_data: "cov-insufficient-data",
  expert_required: "cov-expert",
  // legacy aliases (pre-WP-R4 snapshots)
  done: "cov-no-findings",
  not_done: "cov-not-checked",
  partial: "cov-insufficient-data",
  needs_expert: "cov-expert",
};

const FILTER_OPTIONS = [
  { value: "all", label: "Все состояния" },
  { value: "no_findings", label: "Нарушений не найдено" },
  { value: "findings", label: "Есть находки" },
  { value: "not_checked", label: "Не проверялось" },
  { value: "insufficient_data", label: "Недостаточно данных" },
  { value: "expert_required", label: "Нужен эксперт" },
] as const;

type FilterValue = (typeof FILTER_OPTIONS)[number]["value"];

function formatFamily(key: string): string {
  return key.replaceAll("-", " ").replaceAll("_", " ");
}

function cellStatus(row: CheckCoverageMap["sources"][number], fam: string): string {
  return (
    row.presentation_status?.[fam] ??
    row.operator_status?.[fam] ??
    row.families[fam] ??
    "not_checked"
  );
}

export interface CoverageMapPanelProps {
  reportId: string;
  /** When set, scroll/focus issues list for this family (findings link). */
  onNavigateToFindings?: () => void;
}

/** Per-source × check-family coverage — honesty surface for KT#2 (not product accuracy). */
export default function CoverageMapPanel({
  reportId,
  onNavigateToFindings,
}: CoverageMapPanelProps) {
  const [map, setMap] = useState<CheckCoverageMap | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<FilterValue>("all");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    void fetchReportCoverage(reportId)
      .then((payload) => {
        if (!cancelled) setMap(payload);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setMap(null);
          setError(err instanceof Error ? err.message : "Failed to load coverage");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reportId]);

  const familyKeys = useMemo(
    () =>
      Array.from(
        new Set(
          (map?.sources ?? []).flatMap((row) =>
            Object.keys(row.operator_status ?? row.families ?? {}),
          ),
        ),
      ).sort(),
    [map],
  );

  const filteredSources = useMemo(() => {
    if (!map || statusFilter === "all") return map?.sources ?? [];
    return map.sources.filter((row) =>
      familyKeys.some((fam) => cellStatus(row, fam) === statusFilter),
    );
  }, [map, statusFilter, familyKeys]);

  if (loading) {
    return (
      <section className="coverage-map" data-testid="coverage-map">
        <h3>Карта покрытия проверок</h3>
        <p className="compact-copy">Загрузка…</p>
      </section>
    );
  }

  if (error || !map) {
    return (
      <section className="coverage-map" data-testid="coverage-map">
        <h3>Карта покрытия проверок</h3>
        <p className="compact-copy">
          {error ?? "Coverage unavailable"} — «нет карты» ≠ «всё проверено».
        </p>
      </section>
    );
  }

  return (
    <section className="coverage-map" data-testid="coverage-map">
      <div className="coverage-map-header">
        <h3>Карта покрытия проверок</h3>
        <p className="compact-copy">
          По каждому файлу и семейству: no_findings / findings / not_checked /
          insufficient_data / expert_required. Не смешивать с <code>summary.passed</code>.
        </p>
        <label className="coverage-filter">
          Состояние
          <select
            data-testid="coverage-status-filter"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as FilterValue)}
          >
            {FILTER_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {map.tz_gaps && map.tz_gaps.length > 0 && (
        <table className="coverage-table coverage-tz-gaps" data-testid="coverage-tz-gaps">
          <caption className="compact-copy">Пробелы матрицы ТЗ (всегда честные not_checked)</caption>
          <thead>
            <tr>
              <th scope="col">Раздел</th>
              <th scope="col">Статус</th>
              <th scope="col">Причина</th>
            </tr>
          </thead>
          <tbody>
            {map.tz_gaps.map((gap) => (
              <tr key={gap.gap_id}>
                <td>{gap.label}</td>
                <td className={STATUS_CLASS[gap.status] ?? ""}>
                  <code>{gap.status}</code>
                </td>
                <td className="cov-reason">{gap.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {map.operator_legend && (
        <ul className="coverage-legend compact-copy">
          {Object.entries(map.operator_legend).map(([key, text]) => (
            <li key={key}>
              <code className={STATUS_CLASS[key] ?? ""}>{key}</code> — {text}
            </li>
          ))}
        </ul>
      )}

      {filteredSources.length === 0 ? (
        <p className="compact-copy">Нет строк для выбранного фильтра.</p>
      ) : (
        <table className="coverage-table">
          <thead>
            <tr>
              <th scope="col">Источник</th>
              {familyKeys.map((fam) => (
                <th key={fam} scope="col">
                  {formatFamily(fam)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredSources.map((row) => (
              <tr key={row.source_id}>
                <td>
                  <code>{row.source_id}</code>
                </td>
                {familyKeys.map((fam) => {
                  const op = cellStatus(row, fam);
                  const reason = row.reasons?.[fam];
                  const isFindings = op === "findings";
                  return (
                    <td
                      key={fam}
                      className={STATUS_CLASS[op] ?? ""}
                      title={reason ?? undefined}
                    >
                      {isFindings && onNavigateToFindings ? (
                        <button
                          type="button"
                          className="coverage-findings-link"
                          onClick={onNavigateToFindings}
                        >
                          <code>{op}</code> → находки
                        </button>
                      ) : (
                        <code>{op}</code>
                      )}
                      {reason ? <span className="cov-reason"> {reason}</span> : null}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
