import { Component, type ErrorInfo, type ReactNode } from "react";
import { UI_COPY } from "../../lib/ui-copy";

type Props = { children: ReactNode };
type State = { error: Error | null };

/**
 * Граница ошибок для IFC-вьюера (web-ifc / Three.js).
 *
 * `<Suspense>` ловит только Promise-throws (lazy load). Если WASM-движок
 * бросает синхронную ошибку в render или в обработчике DOM — React без границы
 * размонтирует всё дерево приложения. Граница изолирует сбой: оболочка отчёта
 * (список находок, замечания, экспорт) продолжает работать.
 *
 * Не заменяет обработку ошибок в самом `IfcViewerPanel` (async init / load):
 * там ошибки ловятся в `useEffect` и отображаются через `viewerError`.
 */
export default class IfcViewerErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // В production не отдаём стек наружу; в dev — в консоль для диагностики.
    if (process.env.NODE_ENV !== "production") {
      console.error("[IfcViewerErrorBoundary] render error:", error, info.componentStack);
    }
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div className="panel viewer-error-fallback" role="alert" data-testid="ifc-viewer-error-boundary">
          <p className="compact-copy">{UI_COPY.viewerRenderError}</p>
          <p className="compact-copy">{UI_COPY.viewerRenderErrorHint}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
