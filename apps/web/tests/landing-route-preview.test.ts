import { describe, expect, it } from "vitest";
import { createLandingRoutePreview } from "../src/lib/domain/landing-route-preview";

describe("landing route preview", () => {
  it("selects a route using the supplied random value", () => {
    const first = createLandingRoutePreview(() => 0);
    const last = createLandingRoutePreview(() => 0.999);

    expect(first.number).toBe("0138");
    expect(last.number).toBe("1066");
    expect(first).not.toEqual(last);
  });

  it("offers a varied route across every landing sample", () => {
    const previews = Array.from({ length: 10 }, (_, index) =>
      createLandingRoutePreview(() => (index + 0.5) / 10),
    );

    expect(new Set(previews.map((preview) => preview.start)).size).toBe(10);
    expect(new Set(previews.map((preview) => preview.categoryPath)).size).toBe(
      10,
    );
  });

  it("conceals every connecting step while keeping both endpoints", () => {
    const preview = createLandingRoutePreview(() => 0);
    const connectingSteps = preview.steps.slice(1, -1);

    expect(preview.steps[0]).toMatchObject({
      label: preview.start,
      hidden: false,
    });
    expect(preview.steps.at(-1)).toMatchObject({
      label: preview.target,
      hidden: false,
    });
    expect(connectingSteps).toHaveLength(preview.moves - 1);
    expect(connectingSteps.every((step) => step.hidden)).toBe(true);
    expect(connectingSteps.every((step) => step.label === "…")).toBe(true);
  });
});
