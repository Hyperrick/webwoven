import type { Category, Difficulty, RoundFilters } from "../api/types";
import {
  CATEGORIES,
  categoryPresentation,
  isCategory,
} from "../domain/categories";

export const ANY_CATEGORY = "any" as const;
export type CategoryFilter = Category | typeof ANY_CATEGORY;

export const CATEGORY_FILTER_OPTIONS: ReadonlyArray<{
  value: Category;
  label: string;
}> = CATEGORIES.map((value) => ({
  value,
  label: categoryPresentation(value).label,
}));

type CategoryScope = "solo" | "relay";
type StorageReader = Pick<Storage, "getItem">;
type StorageWriter = Pick<Storage, "setItem">;

function storageKey(scope: CategoryScope): string {
  return `webwoven.category.${scope}`;
}

export function loadCategoryFilter(
  scope: CategoryScope,
  storage: StorageReader = window.localStorage,
): CategoryFilter {
  const value = storage.getItem(storageKey(scope));
  return value !== null && isCategory(value) ? value : ANY_CATEGORY;
}

export function persistCategoryFilter(
  scope: CategoryScope,
  category: CategoryFilter,
  storage: StorageWriter = window.localStorage,
): void {
  storage.setItem(storageKey(scope), category);
}

export function selectedCategory(filter: CategoryFilter): Category | undefined {
  return filter === ANY_CATEGORY ? undefined : filter;
}

export function roundFilters(
  difficulty: Difficulty,
  filter: CategoryFilter,
): RoundFilters {
  const category = selectedCategory(filter);
  return { difficulty, ...(category ? { category } : {}) };
}
