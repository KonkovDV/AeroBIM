import { UI_COPY } from "../../lib/ui-copy";
import { requestFailureBody } from "../../lib/request-failure-copy";
import type { RequestFailureKind } from "../../lib/request-failure";

export type ErrorBannerProps = {
  kind: RequestFailureKind;
  onRetry: () => void;
};

export default function ErrorBanner({ kind, onRetry }: ErrorBannerProps) {
  return (
    <section className="error-banner product-error" role="alert" data-testid="error-banner" data-kind={kind}>
      <div>
        <strong>{UI_COPY.errorBannerTitle}</strong>
        <p>{requestFailureBody(kind)}</p>
      </div>
      <button type="button" className="toolbar-button" onClick={onRetry}>{UI_COPY.retry}</button>
    </section>
  );
}
