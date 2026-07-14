import { describe, expect, it } from "vitest";
import { shouldReduceMotion } from "../src/lib/preferences/preferences";

describe("motion preference", () => {
  it("honors either the in-app or operating-system request", () => {
    expect(shouldReduceMotion(true, false)).toBe(true);
    expect(shouldReduceMotion(false, true)).toBe(true);
    expect(shouldReduceMotion(false, false)).toBe(false);
  });
});
