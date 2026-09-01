import { useEffect, useMemo, useState } from "react";
import { fetchRevisionDiff, type RevisionDiffPayload } from "../lib/api";
import type { ReportSummaryEntry } from "../lib/types";

export type VersionDiffPanelProps = {
  reports: ReportSummaryEntry[];
};

function Bucket({
  title,
  keys,
  testId,
}: {
  title: string;
  keys: string[];
  testId: string;
}) {
  return (
    <article className="detail-block" data-testid={testId}>
      <h3>
        {title} ({keys.length})
      </h3>
      {keys.length === 0 ? (
        <p className="compact-copy">Пусто.</p>
      ) : (
        <ul className="kpi-list">
          {keys.map((key) => (
            <li key={key}>
              <code>{key}</code>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

export default function VersionDiffPanel({ reports }: VersionDiffPanelProps) {
  const sorted = useMemo(
    () =>
      [...reports].sort((left, right) => {
        const leftTs = Date.parse(left.created_at) || 0;
        const rightTs = Date.parse(right.created_at) || 0;
        return leftTs - rightTs;
      }),
    [reports],
  );
  const [baselineId, setBaselineId] = useState<string | null>(null);
  const [headId, setHeadId] = useState<string | null>(null);
  const [diff, setDiff] = useState<RevisionDiffPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const effectiveBaseline = baselineId ?? sorted[0]?.report_id ?? "";
  const effectiveHead =
    headId ??
    [...sorted].reverse().find((row) => row.report_id !== effectiveBaseline)?.report_id ??
    "";

  useEffect(() => {
    if (!effectiveBaseline || !effectiveHead || effectiveBaseline === effectiveHead) {
      setDiff(null);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    fetchRevisionDiff(effectiveBaseline, effectiveHead, { signal: controller.signal })
      .then((payload) => {
        if (!controller.signal.aborted) {
          setDiff(payload);
        }
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "Revision diff failed");
          setDiff(null);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [effectiveBaseline, effectiveHead]);

  return (
    <section className="panel" data-testid="version-diff-panel">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">SCR-DIFF</p>
          <h2>Сравнение версий комплекта</h2>
        </div>
      </div>
      <p className="compact-copy">
        Дельта находок между двумя сохранёнными отчётами.{" "}
        <strong>no_longer_reported ≠ исправлено</strong> — проверка могла не выполниться повторно.
        «Вернулись» требует трёх ревизий; этот экран сравнивает две. Не пишет{" "}
        <code>summary.passed</code>. Checkpoint NO_GO.
      </p>
      {sorted.length < 2 ? (
        <p className="compact-copy">Нужны два сохранённых отчёта. Загрузите и прогоните комплект дважды.</p>
      ) : (
        <div className="report-filters">
          <label>
            База
            <select
              aria-label="Baseline report"
              value={effectiveBaseline}
              onChange={(event) => setBaselineId(event.target.value)}
            >
              {sorted.map((row) => (
                <option key={`b-${row.report_id}`} value={row.report_id}>
                  {row.created_at} · {row.report_id.slice(0, 8)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Сравнение
            <select
              aria-label="Head report"
              value={effectiveHead}
              onChange={(event) => setHeadId(event.target.value)}
            >
              {sorted.map((row) => (
                <option key={`h-${row.report_id}`} value={row.report_id}>
                  {row.created_at} · {row.report_id.slice(0, 8)}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}
      {loading ? <p className="compact-copy">Считаем дельту…</p> : null}
      {error ? (
        <p className="compact-copy" role="alert">
          {error}
        </p>
      ) : null}
      {diff ? (
        <>
          <p className="compact-copy">{diff.note}</p>
          <div className="summary-grid">
            <article className="summary-tile">
              <span>Новые</span>
              <strong>{diff.summary.newly_reported}</strong>
            </article>
            <article className="summary-tile">
              <span>Исчезли</span>
              <strong>{diff.summary.no_longer_reported}</strong>
            </article>
            <article className="summary-tile">
              <span>Сохранились</span>
              <strong>{diff.summary.still_reported}</strong>
            </article>
          </div>
          <Bucket title="Новые" keys={diff.newly_reported} testId="diff-newly-reported" />
          <Bucket title="Исчезли (≠ исправлено)" keys={diff.no_longer_reported} testId="diff-no-longer-reported" />
          <Bucket title="Сохранились" keys={diff.still_reported} testId="diff-still-reported" />
        </>
      ) : null}
    </section>
  );
}
