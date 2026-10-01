/** Lab git-fixture seed UI. Production builds must not offer POST /v1/demo/seed-fixture. */

export function isLabDemoSeedUiEnabled(): boolean {
  return import.meta.env.DEV === true;
}
