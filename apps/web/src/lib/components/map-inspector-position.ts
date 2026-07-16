export interface MapInspectorAnchor {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface MapInspectorPlacement {
  left: number;
  top: number;
}

interface MapInspectorPlacementInput {
  anchor: MapInspectorAnchor;
  panelWidth: number;
  panelHeight: number;
  viewportWidth: number;
  viewportHeight: number;
  gap?: number;
  padding?: number;
}

/** Places the inspector beside its node, flipping and clamping at viewport edges. */
export function placeMapInspector({
  anchor,
  panelWidth,
  panelHeight,
  viewportWidth,
  viewportHeight,
  gap = 12,
  padding = 16,
}: MapInspectorPlacementInput): MapInspectorPlacement {
  const rightCandidate = anchor.left + anchor.width + gap;
  const leftCandidate = anchor.left - gap - panelWidth;
  const rightSpace = viewportWidth - padding - rightCandidate;
  const leftSpace = anchor.left - gap - padding;

  let left: number;
  if (panelWidth <= rightSpace) left = rightCandidate;
  else if (panelWidth <= leftSpace) left = leftCandidate;
  else left = rightSpace >= leftSpace ? rightCandidate : leftCandidate;

  const maximumLeft = Math.max(padding, viewportWidth - padding - panelWidth);
  const maximumTop = Math.max(padding, viewportHeight - padding - panelHeight);
  const centeredTop = anchor.top + anchor.height / 2 - panelHeight / 2;

  return {
    left: Math.round(clamp(left, padding, maximumLeft)),
    top: Math.round(clamp(centeredTop, padding, maximumTop)),
  };
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(Math.max(value, minimum), maximum);
}
