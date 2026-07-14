import { describe, expect, it } from "vitest";
import {
  ROUND_INTRO_DURATION_MS,
  roundIntroTimeline,
} from "../src/lib/round-intro/timeline";

describe("round intro timeline", () => {
  const startsAt = Date.parse("2026-07-15T12:00:05Z");
  const introStart = startsAt - ROUND_INTRO_DURATION_MS;

  it.each([
    [0, "category"],
    [1_249, "category"],
    [1_250, "endpoints"],
    [3_250, "orientation"],
    [4_550, "launch"],
    [5_000, "complete"],
  ] as const)("maps %sms to the %s phase", (offset, phase) => {
    expect(roundIntroTimeline(startsAt, introStart + offset).phase).toBe(phase);
  });

  it("advances late responses and completes resumed sessions immediately", () => {
    expect(roundIntroTimeline(startsAt, startsAt - 400)).toMatchObject({
      phase: "launch",
      remaining_ms: 400,
    });
    expect(roundIntroTimeline(startsAt, startsAt + 1).phase).toBe("complete");
  });
});
