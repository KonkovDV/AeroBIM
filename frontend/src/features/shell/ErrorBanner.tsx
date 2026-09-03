import { UI_COPY } from "../../lib/ui-copy";

export type ErrorBannerProps = {
  message: string;
  onRetry: () => void;
};

/** Отказ API: честный текст + повтор запроса. Не маскирует 501 OIDC. */
export default function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <section className="error-banner" role="alert" data-testid="error-banner">
      <span>{message}</span>
      <button type="button" className="toolbar-button" onClick={onRetry}>
        {UI_COPY.retry}
      </button>
    </section>
  );
}
