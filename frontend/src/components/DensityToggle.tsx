import { useCallback, useEffect, useState } from "react";
import { UI_COPY } from "../lib/ui-copy";
import {
  applyDensity,
  browserDensityStore,
  documentDensityTarget,
  nextDensity,
  persistDensity,
  readStoredDensity,
  type DensityMode,
} from "../lib/ui-density";

/**
 * Переключатель плотности списков.
 *
 * На разборе сотни находок читают с ноутбука, а на защите - с проектора.
 * Одна плотность не закрывает оба сценария, поэтому шагов два, а выбор
 * переживает перезагрузку. Режим меняет только отступы: кегль, контраст
 * и панели честности остаются нетронутыми.
 */
export default function DensityToggle() {
  const [mode, setMode] = useState<DensityMode>(() => readStoredDensity(browserDensityStore()));

  useEffect(() => {
    applyDensity(documentDensityTarget(), mode);
  }, [mode]);

  const toggle = useCallback(() => {
    setMode((current) => persistDensity(browserDensityStore(), nextDensity(current)));
  }, []);

  const compact = mode === "compact";
  const currentLabel = compact ? UI_COPY.densityCompact : UI_COPY.densityComfortable;
  const nextLabel = compact ? UI_COPY.densityComfortable : UI_COPY.densityCompact;

  return (
    <>
      <button
        type="button"
        className="toolbar-button density-toggle"
        data-testid="density-toggle"
        aria-pressed={compact}
        title={UI_COPY.densityHint(nextLabel)}
        onClick={toggle}
      >
        <span className="density-toggle-label">{UI_COPY.densityLabel}</span>
        <span className="density-toggle-value">{currentLabel}</span>
      </button>
      <span
        className="visually-hidden"
        role="status"
        aria-live="polite"
        data-testid="density-announce"
      >
        {UI_COPY.densityAnnounce(currentLabel)}
      </span>
    </>
  );
}
