import { describe, expect, it } from "vitest";
import {
  CATEGORIES,
  categoryPresentation,
  isCategory,
} from "../src/lib/domain/categories";

describe("atlas categories", () => {
  it("publishes ten distinct labels and accents", () => {
    const presentations = CATEGORIES.map(categoryPresentation);

    expect(CATEGORIES).toHaveLength(10);
    expect(new Set(presentations.map(({ label }) => label)).size).toBe(10);
    expect(new Set(presentations.map(({ accent }) => accent)).size).toBe(10);
  });

  it("recognizes only canonical category identifiers", () => {
    expect(CATEGORIES.every(isCategory)).toBe(true);
    expect(isCategory("arts_culture")).toBe(false);
    expect(isCategory("unknown")).toBe(false);
  });
});
