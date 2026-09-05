/** Custom header CSRF for BFF cookie mutations. Value is public, not a secret. */

export const AEROBIM_CSRF_HEADER = "X-AeroBIM-Requested-With";
export const AEROBIM_CSRF_VALUE = "AeroBIMReviewShell";

export function aerobimCsrfHeaders(): Record<string, string> {
  return { [AEROBIM_CSRF_HEADER]: AEROBIM_CSRF_VALUE };
}
