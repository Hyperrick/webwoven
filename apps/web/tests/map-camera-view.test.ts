import { describe, expect, it } from "vitest";
import {
  isRenderableMapCameraView,
  mapCameraViewsEqual,
  visibleMapCameraRect,
  type MapCameraView,
} from "../src/lib/map-camera/map-camera-view";

const view: MapCameraView = {
  x: -200,
  y: -100,
  zoom: 2,
  world_width: 1_600,
  world_height: 900,
  viewport_width: 800,
  viewport_height: 600,
};

describe("map camera view", () => {
  it("derives the exact visible world rectangle", () => {
    const rect = visibleMapCameraRect(view);

    expect(rect).toEqual({ x: 100, y: 50, width: 400, height: 300 });
    expect(view.x + view.zoom * rect.x).toBe(0);
    expect(view.y + view.zoom * rect.y).toBe(0);
    expect(view.x + view.zoom * (rect.x + rect.width)).toBe(
      view.viewport_width,
    );
    expect(view.y + view.zoom * (rect.y + rect.height)).toBe(
      view.viewport_height,
    );
  });

  it("rejects camera states that cannot be rendered", () => {
    expect(isRenderableMapCameraView(view)).toBe(true);
    expect(isRenderableMapCameraView({ ...view, zoom: 0 })).toBe(false);
    expect(
      isRenderableMapCameraView({ ...view, viewport_width: Number.NaN }),
    ).toBe(false);
  });

  it("compares camera values rather than object identity", () => {
    expect(mapCameraViewsEqual({ ...view }, view)).toBe(true);
    expect(mapCameraViewsEqual({ ...view, x: view.x + 1 }, view)).toBe(false);
    expect(mapCameraViewsEqual(null, view)).toBe(false);
  });
});
