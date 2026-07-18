export type MobileChoiceLabelMeasure = (lineCount: number) => void;

/** Observe the natural wrapped line count without constraining the label text. */
export function observeMobileChoiceLabel(
  node: HTMLElement,
  onMeasure: MobileChoiceLabelMeasure,
): { destroy: () => void } {
  let active = true;
  let previousLineCount = 0;

  const measure = (): void => {
    if (!active) return;
    const style = getComputedStyle(node);
    const parsedLineHeight = Number.parseFloat(style.lineHeight);
    const fontSize = Number.parseFloat(style.fontSize);
    const lineHeight = Number.isFinite(parsedLineHeight)
      ? parsedLineHeight
      : fontSize * 1.05;
    if (!Number.isFinite(lineHeight) || lineHeight <= 0) return;
    const lineCount = Math.max(1, Math.round(node.scrollHeight / lineHeight));
    if (lineCount === previousLineCount) return;
    previousLineCount = lineCount;
    onMeasure(lineCount);
  };

  const observer = new ResizeObserver(measure);
  observer.observe(node);
  measure();
  document.fonts.addEventListener("loadingdone", measure);
  void document.fonts.ready.then(measure);

  return {
    destroy: () => {
      active = false;
      observer.disconnect();
      document.fonts.removeEventListener("loadingdone", measure);
    },
  };
}
