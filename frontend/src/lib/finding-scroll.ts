/** Смещение списка, чтобы выбранная строка вошла в окно. Не скроллит, если уже видна. */

export function computeScrollTopToReveal(
  selectedPos: number,
  itemHeight: number,
  viewportHeight: number,
  scrollTop: number,
): number {
  if (selectedPos < 0 || itemHeight <= 0 || viewportHeight <= 0) {
    return scrollTop;
  }
  const top = selectedPos * itemHeight;
  const bottom = top + itemHeight;
  if (top < scrollTop) {
    return top;
  }
  if (bottom > scrollTop + viewportHeight) {
    return Math.max(0, bottom - viewportHeight);
  }
  return scrollTop;
}
