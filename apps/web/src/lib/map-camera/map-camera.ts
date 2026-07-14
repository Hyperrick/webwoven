import type { MapCameraView } from "./map-camera-view";

export const MAP_MIN_ZOOM = 0.1;
export const MAP_MAX_ZOOM = 2;
const MAP_OVERVIEW_GUTTER_FACTOR = 0.5;

export interface MapCameraState {
  x: number;
  y: number;
  zoom: number;
}

export interface MapPoint {
  x: number;
  y: number;
}

export interface MapSize {
  width: number;
  height: number;
}

export interface MapWorldRect {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

export interface MapCameraEnvironment {
  viewport: MapSize;
  world: MapSize;
}

interface FitOptions {
  padding?: number;
  maximumZoom?: number;
}

export function cameraView(
  camera: MapCameraState,
  environment: MapCameraEnvironment,
): MapCameraView {
  return {
    ...camera,
    world_width: environment.world.width,
    world_height: environment.world.height,
    viewport_width: environment.viewport.width,
    viewport_height: environment.viewport.height,
  };
}

export function clampCamera(
  camera: MapCameraState,
  environment: MapCameraEnvironment,
): MapCameraState {
  const zoom = clampZoom(camera.zoom, minimumMapZoom(environment));
  return {
    x: clampAxis(
      camera.x,
      environment.world.width,
      environment.viewport.width,
      zoom,
    ),
    y: clampAxis(
      camera.y,
      environment.world.height,
      environment.viewport.height,
      zoom,
    ),
    zoom,
  };
}

export function panCamera(
  camera: MapCameraState,
  delta: MapPoint,
  environment: MapCameraEnvironment,
): MapCameraState {
  return clampCamera(
    { ...camera, x: camera.x + delta.x, y: camera.y + delta.y },
    environment,
  );
}

/** Pan horizontally so a world coordinate lands at a chosen viewport position. */
export function panCameraToWorldX(
  camera: MapCameraState,
  worldX: number,
  screenX: number,
  environment: MapCameraEnvironment,
): MapCameraState {
  if (!Number.isFinite(worldX) || !Number.isFinite(screenX)) {
    return clampCamera(camera, environment);
  }
  return clampCamera(
    { ...camera, x: screenX - worldX * camera.zoom },
    environment,
  );
}

/** Pan so one world point lands at a chosen viewport point without zooming. */
export function panCameraToWorldPoint(
  camera: MapCameraState,
  worldPoint: MapPoint,
  screenPoint: MapPoint,
  environment: MapCameraEnvironment,
): MapCameraState {
  if (
    ![worldPoint.x, worldPoint.y, screenPoint.x, screenPoint.y].every(
      Number.isFinite,
    )
  ) {
    return clampCamera(camera, environment);
  }
  return {
    ...camera,
    x: screenPoint.x - worldPoint.x * camera.zoom,
    y: screenPoint.y - worldPoint.y * camera.zoom,
  };
}

export function zoomCameraAt(
  camera: MapCameraState,
  nextZoom: number,
  anchor: MapPoint,
  environment: MapCameraEnvironment,
): MapCameraState {
  const zoom = clampZoom(nextZoom, minimumMapZoom(environment));
  const worldPoint = screenToWorld(camera, anchor);
  return clampCamera(
    {
      x: anchor.x - worldPoint.x * zoom,
      y: anchor.y - worldPoint.y * zoom,
      zoom,
    },
    environment,
  );
}

export function gestureCamera(
  camera: MapCameraState,
  previousAnchor: MapPoint,
  nextAnchor: MapPoint,
  zoomFactor: number,
  environment: MapCameraEnvironment,
): MapCameraState {
  const worldPoint = screenToWorld(camera, previousAnchor);
  const zoom = clampZoom(camera.zoom * zoomFactor, minimumMapZoom(environment));
  return clampCamera(
    {
      x: nextAnchor.x - worldPoint.x * zoom,
      y: nextAnchor.y - worldPoint.y * zoom,
      zoom,
    },
    environment,
  );
}

export function cameraForBounds(
  bounds: MapWorldRect,
  environment: MapCameraEnvironment,
  options: FitOptions = {},
): MapCameraState {
  const padding = Math.max(0, options.padding ?? 40);
  const availableWidth = Math.max(1, environment.viewport.width - padding * 2);
  const availableHeight = Math.max(
    1,
    environment.viewport.height - padding * 2,
  );
  const boundsWidth = Math.max(1, bounds.right - bounds.left);
  const boundsHeight = Math.max(1, bounds.bottom - bounds.top);
  const minimumZoom = minimumMapZoom(environment);
  const maximumZoom = clamp(
    options.maximumZoom ?? MAP_MAX_ZOOM,
    minimumZoom,
    MAP_MAX_ZOOM,
  );
  const zoom = clamp(
    Math.min(availableWidth / boundsWidth, availableHeight / boundsHeight),
    minimumZoom,
    maximumZoom,
  );
  return clampCamera(
    {
      x:
        environment.viewport.width / 2 -
        ((bounds.left + bounds.right) / 2) * zoom,
      y:
        environment.viewport.height / 2 -
        ((bounds.top + bounds.bottom) / 2) * zoom,
      zoom,
    },
    environment,
  );
}

export function ensureBoundsVisible(
  camera: MapCameraState,
  bounds: MapWorldRect,
  environment: MapCameraEnvironment,
  padding = 40,
): MapCameraState {
  const availableWidth = Math.max(1, environment.viewport.width - padding * 2);
  const availableHeight = Math.max(
    1,
    environment.viewport.height - padding * 2,
  );
  const width = (bounds.right - bounds.left) * camera.zoom;
  const height = (bounds.bottom - bounds.top) * camera.zoom;
  if (width > availableWidth || height > availableHeight) {
    return cameraForBounds(bounds, environment, {
      padding,
      maximumZoom: camera.zoom,
    });
  }

  const screenLeft = camera.x + bounds.left * camera.zoom;
  const screenRight = camera.x + bounds.right * camera.zoom;
  const screenTop = camera.y + bounds.top * camera.zoom;
  const screenBottom = camera.y + bounds.bottom * camera.zoom;
  let x = camera.x;
  let y = camera.y;
  if (screenLeft < padding) x += padding - screenLeft;
  else if (screenRight > environment.viewport.width - padding)
    x -= screenRight - (environment.viewport.width - padding);
  if (screenTop < padding) y += padding - screenTop;
  else if (screenBottom > environment.viewport.height - padding)
    y -= screenBottom - (environment.viewport.height - padding);
  return clampCamera({ ...camera, x, y }, environment);
}

export function screenToWorld(
  camera: MapCameraState,
  point: MapPoint,
): MapPoint {
  return {
    x: (point.x - camera.x) / camera.zoom,
    y: (point.y - camera.y) / camera.zoom,
  };
}

/**
 * Derive an overview-safe floor that scales with an ever-widening world.
 * The gutter factor leaves enough room for Fit-map padding on narrow screens.
 */
export function minimumMapZoom(environment: MapCameraEnvironment): number {
  const { viewport, world } = environment;
  if (
    ![viewport.width, viewport.height, world.width, world.height].every(
      (value) => Number.isFinite(value) && value > 0,
    )
  )
    return MAP_MIN_ZOOM;
  const overviewFloor = Math.min(
    (viewport.width / world.width) * MAP_OVERVIEW_GUTTER_FACTOR,
    (viewport.height / world.height) * MAP_OVERVIEW_GUTTER_FACTOR,
  );
  return clamp(overviewFloor, Number.EPSILON, MAP_MIN_ZOOM);
}

export function clampZoom(zoom: number, minimumZoom = MAP_MIN_ZOOM): number {
  return clamp(zoom, minimumZoom, MAP_MAX_ZOOM);
}

function clampAxis(
  value: number,
  worldLength: number,
  viewportLength: number,
  zoom: number,
): number {
  if (worldLength <= 0 || viewportLength <= 0) return 0;
  const scaledLength = worldLength * zoom;
  if (scaledLength <= viewportLength)
    return (viewportLength - scaledLength) / 2;
  const overscan = Math.min(96, viewportLength * 0.2);
  return clamp(value, viewportLength - scaledLength - overscan, overscan);
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}
