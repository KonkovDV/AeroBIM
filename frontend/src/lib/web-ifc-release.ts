/** web-ifc FlatMesh/geometry handles sometimes omit `delete` in the browser build. */

export function releaseWebIfcHandle(handle: { delete?: unknown } | null | undefined): void {
  const fn = handle?.delete;
  if (typeof fn === "function") {
    fn.call(handle);
  }
}
