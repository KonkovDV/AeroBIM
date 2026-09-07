import { UI_COPY } from "../../lib/ui-copy";

export type ErrorBannerProps = {
  /** Diagnostics stay in the data layer, never echoed into the workspace. */
  message: string;
  onRetry: () => void;
};

export default function ErrorBanner({ onRetry }: ErrorBannerProps) {
  return (
    <section className="error-banner product-error" role="alert" data-testid="error-banner">
      <div>
        <strong>{UI_COPY.errorBannerTitle}</strong>
        <p>{UI_COPY.errorBannerBody}</p>
      </div>
      <button type="button" className="toolbar-button" onClick={onRetry}>{UI_COPY.retry}</button>
    </section>
  );
}
