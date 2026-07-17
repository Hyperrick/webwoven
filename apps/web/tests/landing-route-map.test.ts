import { describe, expect, it } from "vitest";
import { createLandingRouteMapLayout } from "../src/lib/domain/landing-route-map";

describe("landing route map", () => {
  it("returns the same geometry for the same route seed", () => {
    const first = createLandingRouteMapLayout("0416", 5);
    const second = createLandingRouteMapLayout("0416", 5);

    expect(first).toEqual(second);
    expect(first).not.toEqual(createLandingRouteMapLayout("0924", 5));
  });

  it("keeps waypoints progressing through the safe map area", () => {
    const layout = createLandingRouteMapLayout("0837", 5);

    expect(layout.points).toHaveLength(5);
    for (const [index, point] of layout.points.entries()) {
      expect(point.x).toBeGreaterThanOrEqual(12);
      expect(point.x).toBeLessThanOrEqual(88);
      expect(point.y).toBeGreaterThanOrEqual(14);
      expect(point.y).toBeLessThanOrEqual(83);
      if (index > 0)
        expect(point.x).toBeGreaterThan(layout.points[index - 1].x);
    }
  });

  it("rejects layouts without distinct endpoints", () => {
    expect(() => createLandingRouteMapLayout("0416", 1)).toThrow(RangeError);
  });
});
