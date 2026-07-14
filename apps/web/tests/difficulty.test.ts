import { describe, expect, it } from "vitest";
import {
  loadDifficulty,
  persistDifficulty,
} from "../src/lib/round-setup/difficulty";

describe("difficulty preference", () => {
  it("defaults to Normal and remembers Solo and relay independently", () => {
    const values = new Map<string, string>();
    const storage = {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
    };

    expect(loadDifficulty("solo", storage)).toBe("normal");
    persistDifficulty("solo", "hard", storage);
    persistDifficulty("relay", "easy", storage);
    expect(loadDifficulty("solo", storage)).toBe("hard");
    expect(loadDifficulty("relay", storage)).toBe("easy");
  });
});
