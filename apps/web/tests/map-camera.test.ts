import { describe, expect, it } from "vitest";
import {
  MAP_MAX_ZOOM,
  MAP_MIN_ZOOM,
  cameraForBounds,
  cameraView,
  clampCamera,
  ensureBoundsVisible,
  gestureCamera,
  minimumMapZoom,
  panCamera,
  panCameraToWorldPoint,
  panCameraToWorldX,
  screenToWorld,
  zoomCameraAt,
  type MapCameraEnvironment,
  type MapCameraState,
} from "../src/lib/map-camera/map-camera";

const environment: MapCameraEnvironment = {
  viewport: { width: 800, height: 600 },
  world: { width: 2400, height: 1200 },
};

describe("map camera", () => {
  it("keeps the world point under the pointer fixed while zooming", () => {
    const camera = { x: -360, y: -120, zoom: 0.8 };
    const anchor = { x: 245, y: 318 };
    const before = screenToWorld(camera, anchor);
    const zoomed = zoomCameraAt(camera, 1.25, anchor, environment);

    expect(screenToWorld(zoomed, anchor).x).toBeCloseTo(before.x);
    expect(screenToWorld(zoomed, anchor).y).toBeCloseTo(before.y);
  });

  it("combines pinch translation and scale around the previous midpoint", () => {
    const camera = { x: -240, y: -90, zoom: 0.7 };
    const previous = { x: 300, y: 260 };
    const next = { x: 330, y: 280 };
    const before = screenToWorld(camera, previous);
    const transformed = gestureCamera(camera, previous, next, 1.3, environment);

    expect(screenToWorld(transformed, next).x).toBeCloseTo(before.x);
    expect(screenToWorld(transformed, next).y).toBeCloseTo(before.y);
  });

  it("clamps zoom and keeps an oversized world recoverable", () => {
    const tooFar = clampCamera(
      { x: -100_000, y: 100_000, zoom: MAP_MAX_ZOOM + 4 },
      environment,
    );
    expect(tooFar.zoom).toBe(MAP_MAX_ZOOM);
    expect(tooFar.x).toBeGreaterThan(-environment.world.width * tooFar.zoom);
    expect(tooFar.y).toBeLessThan(environment.viewport.height);

    const tooSmall = clampCamera(
      { x: 0, y: 0, zoom: MAP_MIN_ZOOM / 4 },
      environment,
    );
    expect(tooSmall.zoom).toBe(MAP_MIN_ZOOM);
  });

  it("fits a remote explored branch inside the padded viewport", () => {
    const bounds = { left: 1600, top: 240, right: 2200, bottom: 900 };
    const fitted = cameraForBounds(bounds, environment, {
      padding: 40,
      maximumZoom: 1,
    });
    const left = fitted.x + bounds.left * fitted.zoom;
    const right = fitted.x + bounds.right * fitted.zoom;
    const top = fitted.y + bounds.top * fitted.zoom;
    const bottom = fitted.y + bounds.bottom * fitted.zoom;

    expect(left).toBeGreaterThanOrEqual(39.9);
    expect(right).toBeLessThanOrEqual(760.1);
    expect(top).toBeGreaterThanOrEqual(39.9);
    expect(bottom).toBeLessThanOrEqual(560.1);
  });

  it("fits and retains an overview of a very wide exploration history", () => {
    const wideEnvironment: MapCameraEnvironment = {
      viewport: { width: 320, height: 568 },
      world: { width: 50_000, height: 1_200 },
    };
    const bounds = { left: 200, top: 120, right: 49_800, bottom: 1_080 };
    const fitted = cameraForBounds(bounds, wideEnvironment, {
      padding: 36,
      maximumZoom: 1,
    });

    expect(minimumMapZoom(wideEnvironment)).toBeLessThan(MAP_MIN_ZOOM);
    expect(fitted.zoom).toBeLessThan(MAP_MIN_ZOOM);
    expect(fitted.x + bounds.left * fitted.zoom).toBeGreaterThanOrEqual(35.9);
    expect(fitted.x + bounds.right * fitted.zoom).toBeLessThanOrEqual(284.1);

    const panned = panCamera(fitted, { x: -8, y: 0 }, wideEnvironment);
    expect(panned.zoom).toBe(fitted.zoom);
  });

  it("moves only enough to reveal an offscreen active frontier", () => {
    const camera: MapCameraState = { x: -500, y: -100, zoom: 1 };
    const bounds = { left: 1200, top: 200, right: 1450, bottom: 420 };
    const ensured = ensureBoundsVisible(camera, bounds, environment, 40);

    expect(ensured.zoom).toBe(camera.zoom);
    expect(ensured.x + bounds.right).toBeLessThanOrEqual(760);
    expect(ensured.x).toBeLessThan(camera.x);
  });

  it("pans a new stage to a stable viewport anchor without changing zoom", () => {
    const camera: MapCameraState = { x: -300, y: -100, zoom: 0.8 };
    const panned = panCameraToWorldX(camera, 1200, 220, environment);

    expect(panned.x + 1200 * panned.zoom).toBeCloseTo(220);
    expect(panned.y).toBe(camera.y);
    expect(panned.zoom).toBe(camera.zoom);
  });

  it("centers a returned node on both axes without changing zoom", () => {
    const camera: MapCameraState = { x: -300, y: -100, zoom: 0.8 };
    const centered = panCameraToWorldPoint(
      camera,
      { x: 1_200, y: 500 },
      { x: 400, y: 300 },
      environment,
    );

    expect(centered.x + 1_200 * centered.zoom).toBeCloseTo(400);
    expect(centered.y + 500 * centered.zoom).toBeCloseTo(300);
    expect(centered.zoom).toBe(camera.zoom);
  });

  it("maps presentation state to the renderer contract without drift", () => {
    const camera = { x: -400, y: -160, zoom: 0.65 };
    expect(cameraView(camera, environment)).toEqual({
      ...camera,
      world_width: 2400,
      world_height: 1200,
      viewport_width: 800,
      viewport_height: 600,
    });
  });
});
