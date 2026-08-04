import { useEffect, useState } from "react";
import { fetchReportCoverage, type CheckCoverageMap } from "../lib/api";

const STATUS_CLASS: Record<string, string> = {
  done: "cov-done",
  findings: "cov-findings",
  not_done: "cov-not-done",
  partial: "cov-partial",
  needs_expert: "cov-expert",
};

function formatFamily(key: string): string {
  return key.replaceAll("-", " ").replaceAll("_", " ");
}

export interface CoverageMapPanelProps {
  reportId: string;
}

/** Per-source × check-family coverage — honesty surface for KT#2 (not product accuracy). */
export default function CoverageMapPanel({ reportId }: CoverageMapPanelProps) {
  const [map, setMap] = useState<CheckCoverageMap | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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

  const familyKeys = Array.from(
    new Set(map.sources.flatMap((row) => Object.keys(row.operator_status ?? row.families))),
  ).sort();

  return (
    <section className="coverage-map" data-testid="coverage-map">
      <div className="coverage-map-header">
        <h3>Карта покрытия проверок</h3>
        <p className="compact-copy">
          По каждому файлу и семейству: выполнено / находки / не выполнялось / недостаточно
          данных / нужен эксперт. Не смешивать с <code>summary.passed</code>.
        </p>
      </div>

      {map.operator_legend && (
        <ul className="coverage-legend compact-copy">
          {Object.entries(map.operator_legend).map(([key, text]) => (
            <li key={key}>
              <code className={STATUS_CLASS[key] ?? ""}>{key}</code> — {text}
            </li>
          ))}
        </ul>
      )}

      {map.sources.length === 0 ? (
        <p className="compact-copy">Нет источников в отчёте для карты покрытия.</p>
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
            {map.sources.map((row) => (
              <tr key={row.source_id}>
                <td>
                  <code>{row.source_id}</code>
                </td>
                {familyKeys.map((fam) => {
                  const op =
                    row.operator_status?.[fam] ??
                    row.families[fam] ??
                    "not_done";
                  const reason = row.reasons?.[fam];
                  return (
                    <td key={fam} className={STATUS_CLASS[op] ?? ""} title={reason ?? undefined}>
                      <code>{op}</code>
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
