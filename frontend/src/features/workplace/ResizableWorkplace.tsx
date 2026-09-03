import { useCallback, useEffect, useRef, useState, type PointerEvent, type ReactNode } from "react";
import { UI_COPY } from "../../lib/ui-copy";

const STORAGE_KEY = "aerobim-workspace-cols-v1";
const MIN_PCT = 16;

type Cols = { left: number; mid: number; right: number };

function clampCols(next: Cols): Cols {
  const left = Math.max(MIN_PCT, next.left);
  const right = Math.max(MIN_PCT, next.right);
  const mid = Math.max(MIN_PCT, 100 - left - right);
  const scale = 100 / (left + mid + right);
  return {
    left: Math.round(left * scale * 10) / 10,
    mid: Math.round(mid * scale * 10) / 10,
    right: Math.round(right * scale * 10) / 10,
  };
}

function readCols(): Cols {
  if (typeof window === "undefined") {
    return { left: 28, mid: 36, right: 36 };
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { left: 28, mid: 36, right: 36 };
    }
    const parsed = JSON.parse(raw) as Partial<Cols>;
    return clampCols({
      left: Number(parsed.left) || 28,
      mid: Number(parsed.mid) || 36,
      right: Number(parsed.right) || 36,
    });
  } catch {
    return { left: 28, mid: 36, right: 36 };
  }
}

export type ResizableWorkplaceProps = {
  left: ReactNode;
  center: ReactNode;
  right: ReactNode;
};

export default function ResizableWorkplace({ left, center, right }: ResizableWorkplaceProps) {
  const gridRef = useRef<HTMLElement | null>(null);
  const [cols, setCols] = useState<Cols>(readCols);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(cols));
  }, [cols]);

  const onResize = useCallback((which: "left" | "right", event: PointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    const grid = gridRef.current;
    if (!grid) {
      return;
    }
    const startX = event.clientX;
    const start = { ...cols };
    const width = grid.getBoundingClientRect().width;

    function move(ev: globalThis.PointerEvent): void {
      const deltaPct = ((ev.clientX - startX) / Math.max(width, 1)) * 100;
      if (which === "left") {
        setCols(clampCols({ ...start, left: start.left + deltaPct, mid: start.mid - deltaPct }));
      } else {
        setCols(clampCols({ ...start, mid: start.mid + deltaPct, right: start.right - deltaPct }));
      }
    }

    function up(): void {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    }

    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }, [cols]);

  return (
    <main
      ref={gridRef}
      className="workspace-grid"
      data-testid="workspace-grid"
      style={{
        ["--col-left" as string]: `${cols.left}fr`,
        ["--col-mid" as string]: `${cols.mid}fr`,
        ["--col-right" as string]: `${cols.right}fr`,
      }}
    >
      {left}
      <div
        className="grid-resizer"
        role="separator"
        aria-orientation="vertical"
        aria-label={UI_COPY.resizeLeftAria}
        onPointerDown={(event) => onResize("left", event)}
      />
      {center}
      <div
        className="grid-resizer"
        role="separator"
        aria-orientation="vertical"
        aria-label={UI_COPY.resizeRightAria}
        onPointerDown={(event) => onResize("right", event)}
      />
      {right}
    </main>
  );
}
