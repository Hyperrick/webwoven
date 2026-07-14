/**
 * Camera state in CSS pixels.
 *
 * A world point maps to the viewport as:
 * `screen = (x, y) + zoom * world`.
 */
export interface MapCameraView {
  x: number;
  y: number;
  zoom: number;
  world_width: number;
  world_height: number;
  viewport_width: number;
  viewport_height: number;
}

export interface MapCameraVisibleRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export function isRenderableMapCameraView(view: MapCameraView): boolean {
  return (
    valuesAreFinite(view) &&
    view.zoom > 0 &&
    view.world_width > 0 &&
    view.world_height > 0 &&
    view.viewport_width > 0 &&
    view.viewport_height > 0
  );
}

/** Returns the world-space rectangle currently visible in the viewport. */
export function visibleMapCameraRect(
  view: MapCameraView,
): MapCameraVisibleRect {
  if (!isRenderableMapCameraView(view)) {
    return { x: 0, y: 0, width: 1, height: 1 };
  }
  return {
    x: -view.x / view.zoom,
    y: -view.y / view.zoom,
    width: view.viewport_width / view.zoom,
    height: view.viewport_height / view.zoom,
  };
}

export function mapCameraViewsEqual(
  left: MapCameraView | null,
  right: MapCameraView,
): boolean {
  return Boolean(
    left &&
    left.x === right.x &&
    left.y === right.y &&
    left.zoom === right.zoom &&
    left.world_width === right.world_width &&
    left.world_height === right.world_height &&
    left.viewport_width === right.viewport_width &&
    left.viewport_height === right.viewport_height,
  );
}

function valuesAreFinite(view: MapCameraView): boolean {
  return [
    view.x,
    view.y,
    view.zoom,
    view.world_width,
    view.world_height,
    view.viewport_width,
    view.viewport_height,
  ].every(Number.isFinite);
}
