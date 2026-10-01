/** Max of an index buffer without `Math.max(...arr)` (stack overflow on large meshes). */

export function maxIndexValue(indices: ArrayLike<number>): number {
  let max = -1;
  for (let i = 0; i < indices.length; i += 1) {
    const value = indices[i];
    if (value > max) {
      max = value;
    }
  }
  return max;
}
