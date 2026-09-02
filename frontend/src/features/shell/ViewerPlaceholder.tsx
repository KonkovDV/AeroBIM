import { UI_COPY } from "../../lib/ui-copy";

export default function ViewerPlaceholder({ message }: { message: string }) {
  return (
    <section className="panel viewer-panel viewer-panel-placeholder">
      <div className="panel-header viewer-header">
        <div>
          <p className="panel-kicker">{UI_COPY.viewerKicker}</p>
          <h2>{UI_COPY.viewerTitle}</h2>
        </div>
      </div>
      <div className="viewer-stage">
        <div className="viewer-overlay">
          <p>{message}</p>
        </div>
      </div>
      <p className="viewer-caption">{UI_COPY.viewerCaption}</p>
    </section>
  );
}
