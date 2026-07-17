import { describe, expect, it } from "vitest";
import {
  ANY_CATEGORY,
  CATEGORY_FILTER_OPTIONS,
  loadCategoryFilter,
  persistCategoryFilter,
  roundFilters,
  selectedCategory,
} from "../src/lib/round-setup/category-filter";

function storage(initial: Record<string, string> = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem(key: string): string | null {
      return values.get(key) ?? null;
    },
    setItem(key: string, value: string): void {
      values.set(key, value);
    },
  };
}

describe("category filter", () => {
  it("offers every canonical category after the unfiltered choice", () => {
    expect(CATEGORY_FILTER_OPTIONS).toHaveLength(10);
    expect(
      new Set(CATEGORY_FILTER_OPTIONS.map(({ value }) => value)).size,
    ).toBe(10);
    expect(CATEGORY_FILTER_OPTIONS[0]).toEqual({
      value: "people",
      label: "People",
    });
  });

  it("defaults missing and invalid stored values to any category", () => {
    expect(loadCategoryFilter("solo", storage())).toBe(ANY_CATEGORY);
    expect(
      loadCategoryFilter(
        "relay",
        storage({ "webwoven.category.relay": "unknown" }),
      ),
    ).toBe(ANY_CATEGORY);
  });

  it("keeps Solo and Relay preferences separate", () => {
    const preferences = storage();
    persistCategoryFilter("solo", "science_technology", preferences);
    persistCategoryFilter("relay", "film_media", preferences);

    expect(loadCategoryFilter("solo", preferences)).toBe("science_technology");
    expect(loadCategoryFilter("relay", preferences)).toBe("film_media");
  });

  it("omits any category and returns a selected canonical filter", () => {
    expect(selectedCategory(ANY_CATEGORY)).toBeUndefined();
    expect(selectedCategory("nature_life")).toBe("nature_life");
    expect(roundFilters("normal", ANY_CATEGORY)).toEqual({
      difficulty: "normal",
    });
    expect(roundFilters("hard", "nature_life")).toEqual({
      difficulty: "hard",
      category: "nature_life",
    });
  });
});
