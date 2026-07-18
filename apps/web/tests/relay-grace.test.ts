import { describe, expect, it } from "vitest";
import {
  formatRelayGrace,
  relayGraceDeadline,
  relayGraceRemainingSeconds,
} from "../src/lib/domain/relay-grace";

describe("relay grace timing", () => {
  it("rounds partial seconds up and stops at zero", () => {
    const room = {
      state: "grace_period",
      grace_ends_at: "2026-07-18T12:00:30.000Z",
    };

    expect(
      relayGraceRemainingSeconds(room, Date.parse("2026-07-18T12:00:00.001Z")),
    ).toBe(30);
    expect(
      relayGraceRemainingSeconds(room, Date.parse("2026-07-18T12:00:29.001Z")),
    ).toBe(1);
    expect(
      relayGraceRemainingSeconds(room, Date.parse("2026-07-18T12:00:30.001Z")),
    ).toBe(0);
  });

  it("ignores missing, invalid, and inactive grace deadlines", () => {
    expect(relayGraceDeadline({ state: "grace_period" })).toBeNull();
    expect(
      relayGraceRemainingSeconds(
        { state: "grace_period", grace_ends_at: "not-a-date" },
        Date.now(),
      ),
    ).toBeNull();
    expect(
      relayGraceRemainingSeconds(
        {
          state: "racing",
          grace_ends_at: "2026-07-18T12:00:30.000Z",
        },
        Date.parse("2026-07-18T12:00:00.000Z"),
      ),
    ).toBeNull();
  });

  it("formats a compact clock", () => {
    expect(formatRelayGrace(30)).toBe("00:30");
    expect(formatRelayGrace(1)).toBe("00:01");
    expect(formatRelayGrace(-1)).toBe("00:00");
  });
});
