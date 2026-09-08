import { cloneElement, isValidElement, useEffect, useId, useRef, useState, type KeyboardEvent, type PointerEvent, type ReactNode } from "react";
import { UI_COPY } from "../../lib/ui-copy";
import { DEFAULT_COLS, MIN_PCT, normalizeCols, resizeCols, type Cols, type Side } from "./workspace-columns";
import "./resizable-workplace.css";

const STORAGE_KEY = "aerobim-workspace-cols-v1";

function readCols(): Cols {
  try {
    return normalizeCols(JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "null"));
  } catch {
    return { ...DEFAULT_COLS };
  }
}

function identifyPane(node: ReactNode, fallbackId: string) {
  if (isValidElement<{ id?: string }>(node) && typeof node.type === "string") {
    const id = node.props.id || fallbackId;
    return { id, node: cloneElement(node, { id }) };
  }
  return { id: fallbackId, node: <div id={fallbackId}>{node}</div> };
}

export type ResizableWorkplaceProps = { left: ReactNode; center: ReactNode; right: ReactNode };
type Drag = { side: Side; pointerId: number; x: number; width: number; start: Cols };

export default function ResizableWorkplace({ left, center, right }: ResizableWorkplaceProps) {
  const gridRef = useRef<HTMLElement | null>(null);
  const dragRef = useRef<Drag | null>(null);
  const [cols, setCols] = useState<Cols>(readCols);
  const id = useId();
  const leftPane = identifyPane(left, `${id}-left`);
  const rightPane = identifyPane(right, `${id}-right`);
  const maximum = (side: Side): number => 100 - MIN_PCT - cols[side === "left" ? "right" : "left"];

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(cols));
    } catch {
      // Storage may be disabled; resizing still works for this session.
    }
  }, [cols]);

  function onKey(side: Side, event: KeyboardEvent<HTMLDivElement>): void {
    if (event.defaultPrevented || event.nativeEvent.isComposing || event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key === "Escape" && dragRef.current) {
      const drag = dragRef.current;
      dragRef.current = null;
      setCols(drag.start);
      if (event.currentTarget.hasPointerCapture(drag.pointerId)) event.currentTarget.releasePointerCapture(drag.pointerId);
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    event.stopPropagation();
    const direction = (event.key === "ArrowRight" ? 1 : -1) * (side === "left" ? 1 : -1);
    const value = event.key === "Home" ? MIN_PCT : event.key === "End" ? maximum(side)
      : cols[side] + direction * (event.shiftKey ? 10 : 2);
    setCols((current) => resizeCols(current, side, value));
  }

  function onStart(side: Side, event: PointerEvent<HTMLDivElement>): void {
    const grid = gridRef.current;
    if (!grid || event.button !== 0 || !event.isPrimary || dragRef.current) return;
    // fr units exclude gutters and padding; measure the actual three pane tracks.
    const width = Array.from(grid.children).filter((child) => !child.classList.contains("grid-resizer"))
      .reduce((sum, child) => sum + child.getBoundingClientRect().width, 0);
    if (width <= 0) return;
    event.preventDefault();
    event.currentTarget.focus();
    dragRef.current = { side, pointerId: event.pointerId, x: event.clientX, width, start: cols };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function onMove(event: PointerEvent<HTMLDivElement>): void {
    const drag = dragRef.current;
    if (!drag || event.pointerId !== drag.pointerId) return;
    const delta = (event.clientX - drag.x) / drag.width * 100 * (drag.side === "left" ? 1 : -1);
    setCols(resizeCols(drag.start, drag.side, drag.start[drag.side] + delta));
  }

  function onEnd(event: PointerEvent<HTMLDivElement>, cancel = false): void {
    const drag = dragRef.current;
    if (!drag || event.pointerId !== drag.pointerId) return;
    dragRef.current = null;
    if (cancel) setCols(drag.start);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  function separator(side: Side, paneId: string, label: string) {
    return <div className="grid-resizer" role="separator" tabIndex={0}
      aria-orientation="vertical" aria-label={label} aria-controls={paneId}
      aria-valuemin={MIN_PCT} aria-valuemax={maximum(side)} aria-valuenow={cols[side]}
      aria-describedby={`${id}-help`}
      onKeyDown={(event) => onKey(side, event)} onPointerDown={(event) => onStart(side, event)}
      onPointerMove={onMove} onPointerUp={(event) => onEnd(event)}
      onPointerCancel={(event) => onEnd(event, true)} onLostPointerCapture={(event) => onEnd(event, true)} />;
  }

  return <>
    <details className="workspace-layout-controls">
      <summary>Ширина панелей</summary>
      <div className="workspace-layout-fields">
        <label><span>Список <output aria-hidden="true">{cols.left}%</output></span>
          <input type="range" aria-label="Ширина списка, проценты" min={MIN_PCT} max={maximum("left")}
            step="0.1" value={cols.left} onChange={(event) => setCols(resizeCols(cols, "left", event.target.valueAsNumber))} />
        </label>
        <label><span>Карточка <output aria-hidden="true">{cols.right}%</output></span>
          <input type="range" aria-label="Ширина карточки, проценты" min={MIN_PCT} max={maximum("right")}
            step="0.1" value={cols.right} onChange={(event) => setCols(resizeCols(cols, "right", event.target.valueAsNumber))} />
        </label>
        <button type="button" className="toolbar-button" onClick={() => setCols({ ...DEFAULT_COLS })}>Сбросить ширину</button>
      </div>
      <p id={`${id}-help`}>Нажмите на шкалу без перетаскивания. На разделителе: ←/→ — шаг 2%, <kbd>SHIFT</kbd> — 10%, <kbd>HOME</kbd>/<kbd>END</kbd> — минимум/максимум ширины. <kbd>ESC</kbd> — отмена жеста.</p>
    </details>
    <main ref={gridRef} className="workspace-grid" data-testid="workspace-grid"
      style={{ ["--col-left" as string]: `${cols.left}fr`, ["--col-mid" as string]: `${cols.mid}fr`, ["--col-right" as string]: `${cols.right}fr` }}>
      {leftPane.node}
      {separator("left", leftPane.id, UI_COPY.resizeLeftAria)}
      {center}
      {separator("right", rightPane.id, UI_COPY.resizeRightAria)}
      {rightPane.node}
    </main>
  </>;
}
