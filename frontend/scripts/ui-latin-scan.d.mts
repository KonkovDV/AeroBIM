export const ALLOWED_WORDS: ReadonlySet<string>;
export const TS_SCAN_FILES: string[];
export const TS_ERROR_ONLY_FILES: string[];
export function scanTsxSource(source: string, relPath: string): string[];
export function scanTsSource(
  source: string,
  relPath: string,
  options?: { errorsOnly?: boolean },
): string[];
export function scanDictionaryValue(value: string, relPath: string, key: string): string[];
