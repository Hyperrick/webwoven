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
    [3_250, "zoom_out"],
    [4_550, "handoff"],
    [5_000, "complete"],
  ] as const)("maps %sms to the %s phase", (offset, phase) => {
    expect(roundIntroTimeline(startsAt, introStart + offset).phase).toBe(phase);
  });

  it("advances late responses and completes resumed sessions immediately", () => {
    expect(roundIntroTimeline(startsAt, startsAt - 400)).toMatchObject({
      phase: "handoff",
      remaining_ms: 400,
    });
    expect(roundIntroTimeline(startsAt, startsAt + 1).phase).toBe("complete");
  });

  it("fades the endpoints in before zooming out and handing off", () => {
    expect(roundIntroTimeline(startsAt, introStart + 1_250)).toMatchObject({
      endpoints: 0,
      zoom_out: 0,
      handoff: 0,
    });
    expect(roundIntroTimeline(startsAt, introStart + 3_250)).toMatchObject({
      endpoints: 1,
      zoom_out: 0,
      handoff: 0,
    });
    expect(roundIntroTimeline(startsAt, introStart + 4_550)).toMatchObject({
      endpoints: 1,
      zoom_out: 1,
      handoff: 0,
    });
  });
});
