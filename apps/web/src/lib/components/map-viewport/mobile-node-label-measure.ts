export type MobileNodeLabelMeasure = (lineCount: number) => void;

/** Observe a naturally wrapped mobile node label without constraining its text. */
export function observeMobileNodeLabel(
  node: HTMLElement,
  onMeasure: MobileNodeLabelMeasure,
): { destroy: () => void } {
  let active = true;
  let previousLineCount = 0;
  let animationFrame: number | undefined;

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

  const scheduleMeasure = (): void => {
    if (!active || animationFrame !== undefined) return;
    animationFrame = requestAnimationFrame(() => {
      animationFrame = undefined;
      measure();
    });
  };

  const observer = new ResizeObserver(scheduleMeasure);
  observer.observe(node);
  measure();
  document.fonts.addEventListener("loadingdone", scheduleMeasure);
  void document.fonts.ready.then(scheduleMeasure);

  return {
    destroy: () => {
      active = false;
      if (animationFrame !== undefined) cancelAnimationFrame(animationFrame);
      observer.disconnect();
      document.fonts.removeEventListener("loadingdone", scheduleMeasure);
    },
  };
}
