import { palette } from "@webwoven/design-tokens/tokens";
import type { Category } from "../api/types";

interface CategoryTheme {
  label: string;
  accent: string;
}

const CATEGORY_THEMES: Record<Category, CategoryTheme> = {
  history_people: {
    label: "History & People",
    accent: palette.ochre,
  },
  nature_science: {
    label: "Nature & Science",
    accent: palette.moss,
  },
  arts_culture: {
    label: "Arts & Culture",
    accent: palette.signal,
  },
  places: {
    label: "Places",
    accent: palette.cartographic,
  },
};

export function categoryTheme(category: Category): CategoryTheme {
  return CATEGORY_THEMES[category];
}
