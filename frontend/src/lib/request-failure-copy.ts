import { UI_COPY } from "./ui-copy";
import type { RequestFailureKind } from "./request-failure";

/** Visible recovery copy. Never interpolates URL, status text, or stack. */
export function requestFailureBody(kind: RequestFailureKind): string {
  if (kind === "network") {
    return UI_COPY.errorBannerNetwork;
  }
  if (kind === "forbidden") {
    return UI_COPY.errorBannerForbidden;
  }
  if (kind === "not_found") {
    return UI_COPY.errorBannerNotFound;
  }
  if (kind === "server") {
    return UI_COPY.errorBannerServer;
  }
  return UI_COPY.errorBannerBody;
}
