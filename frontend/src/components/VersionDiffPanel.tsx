import { useEffect, useMemo, useState } from "react";
import { fetchRevisionDiff, type RevisionDiffPayload } from "../lib/api";
import type { ReportSummaryEntry } from "../lib/types";
import { UI_COPY } from "../lib/ui-copy";

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
        <p className="compact-copy">{UI_COPY.diffEmpty}</p>
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
          setError(err instanceof Error ? err.message : UI_COPY.diffFailed);
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
          <p className="panel-kicker">{UI_COPY.diffKicker}</p>
          <h2>{UI_COPY.diffTitle}</h2>
        </div>
      </div>
      <p className="compact-copy">{UI_COPY.diffNote}</p>
      {sorted.length < 2 ? (
        <p className="compact-copy">{UI_COPY.diffNeedTwo}</p>
      ) : (
        <div className="report-filters">
          <label>
            {UI_COPY.diffBaseline}
            <select
              aria-label={UI_COPY.diffBaseline}
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
            {UI_COPY.diffHead}
            <select
              aria-label={UI_COPY.diffHead}
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
      {loading ? <p className="compact-copy">{UI_COPY.diffComputing}</p> : null}
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
              <span>{UI_COPY.diffNew}</span>
              <strong>{diff.summary.newly_reported}</strong>
            </article>
            <article className="summary-tile">
              <span>{UI_COPY.diffGone}</span>
              <strong>{diff.summary.no_longer_reported}</strong>
            </article>
            <article className="summary-tile">
              <span>{UI_COPY.diffStill}</span>
              <strong>{diff.summary.still_reported}</strong>
            </article>
          </div>
          <Bucket title={UI_COPY.diffNew} keys={diff.newly_reported} testId="diff-newly-reported" />
          <Bucket title={UI_COPY.diffGoneNote} keys={diff.no_longer_reported} testId="diff-no-longer-reported" />
          <Bucket title={UI_COPY.diffStill} keys={diff.still_reported} testId="diff-still-reported" />
        </>
      ) : null}
    </section>
  );
}
