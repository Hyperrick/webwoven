import { describe, expect, it } from "vitest";
import { placeMapInspector } from "../src/lib/components/map-inspector-position";

const panel = { panelWidth: 320, panelHeight: 240 };
const viewport = { viewportWidth: 1_200, viewportHeight: 700 };

describe("placeMapInspector", () => {
  it("places the panel to the right of the clicked node when it fits", () => {
    expect(
      placeMapInspector({
        anchor: { left: 240, top: 260, width: 140, height: 80 },
        ...panel,
        ...viewport,
      }),
    ).toEqual({ left: 392, top: 180 });
  });

  it("flips the panel to the left near the right edge", () => {
    expect(
      placeMapInspector({
        anchor: { left: 930, top: 260, width: 140, height: 80 },
        ...panel,
        ...viewport,
      }),
    ).toEqual({ left: 598, top: 180 });
  });

  it("clamps the panel inside the vertical viewport padding", () => {
    expect(
      placeMapInspector({
        anchor: { left: 240, top: 10, width: 140, height: 40 },
        ...panel,
        ...viewport,
      }).top,
    ).toBe(16);

    expect(
      placeMapInspector({
        anchor: { left: 240, top: 660, width: 140, height: 40 },
        ...panel,
        ...viewport,
      }).top,
    ).toBe(444);
  });
});
