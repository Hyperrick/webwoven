import { describe, expect, it } from "vitest";
import { calculateScore, hintPenalty } from "../src/lib/domain/scoring";

describe("route scoring", () => {
  it("awards the maximum for an optimal immediate route", () => {
    expect(
      calculateScore({
        shortestDistance: 4,
        moves: 4,
        elapsedSeconds: 0,
        timeWindow: 180,
        penalties: 0,
      }),
    ).toBe(1000);
  });

  it("weights route efficiency more heavily than time", () => {
    const efficient = calculateScore({
      shortestDistance: 4,
      moves: 4,
      elapsedSeconds: 150,
      timeWindow: 180,
      penalties: 0,
    });
    const fastDetour = calculateScore({
      shortestDistance: 4,
      moves: 8,
      elapsedSeconds: 5,
      timeWindow: 180,
      penalties: 0,
    });
    expect(efficient).toBeGreaterThan(fastDetour);
  });

  it("clamps scores and exposes fixed hint costs", () => {
    expect(
      calculateScore({
        shortestDistance: 4,
        moves: 40,
        elapsedSeconds: 500,
        timeWindow: 180,
        penalties: 900,
      }),
    ).toBe(0);
    expect(hintPenalty("compass")).toBe(75);
    expect(hintPenalty("lens")).toBe(150);
    expect(hintPenalty("map_fragment")).toBe(250);
  });
});
