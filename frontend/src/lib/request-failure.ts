/** Safe categories for the workspace banner. Never carry URL, stack, or body text. */
export type RequestFailureKind =
  | "network"
  | "forbidden"
  | "not_found"
  | "server"
  | "unknown";

function httpStatus(error: unknown): number | null {
  if (typeof error !== "object" || error === null || !("status" in error)) {
    return null;
  }
  const status = (error as { status: unknown }).status;
  return typeof status === "number" ? status : null;
}

export function classifyRequestFailure(error: unknown): RequestFailureKind {
  const status = httpStatus(error);
  if (status === 401 || status === 403) {
    return "forbidden";
  }
  if (status === 404) {
    return "not_found";
  }
  if (status !== null && status >= 500) {
    return "server";
  }
  if (status !== null) {
    return "unknown";
  }
  if (typeof DOMException !== "undefined" && error instanceof DOMException && error.name === "AbortError") {
    return "unknown";
  }
  if (error instanceof TypeError) {
    return "network";
  }
  return "unknown";
}
