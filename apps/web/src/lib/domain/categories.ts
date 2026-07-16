import { palette } from "@webwoven/design-tokens/tokens";
import type { Category } from "../api/types";

export interface CategoryPresentation {
  label: string;
  accent: string;
  fallbackArtwork: string;
}

export const CATEGORIES: readonly Category[] = [
  "people",
  "history_society",
  "science_technology",
  "nature_life",
  "places_architecture",
  "art_design",
  "literature_language",
  "music_performance",
  "film_media",
  "sports_games",
];

export function isCategory(value: string): value is Category {
  return CATEGORIES.some((category) => category === value);
}

export const CATEGORY_PRESENTATION: Record<Category, CategoryPresentation> = {
  people: {
    label: "People",
    accent: palette.signal,
    fallbackArtwork: "/illustrations/history-people.webp",
  },
  history_society: {
    label: "History & Society",
    accent: palette.sienna,
    fallbackArtwork: "/illustrations/history-people.webp",
  },
  science_technology: {
    label: "Science & Technology",
    accent: palette.cartographic,
    fallbackArtwork: "/illustrations/nature-science.webp",
  },
  nature_life: {
    label: "Nature & Life",
    accent: palette.moss,
    fallbackArtwork: "/illustrations/nature-science.webp",
  },
  places_architecture: {
    label: "Places & Architecture",
    accent: palette.ochre,
    fallbackArtwork: "/illustrations/places.webp",
  },
  art_design: {
    label: "Art & Design",
    accent: palette.copper,
    fallbackArtwork: "/illustrations/arts-culture.webp",
  },
  literature_language: {
    label: "Literature & Language",
    accent: palette.olive,
    fallbackArtwork: "/illustrations/arts-culture.webp",
  },
  music_performance: {
    label: "Music & Performance",
    accent: palette.teal,
    fallbackArtwork: "/illustrations/arts-culture.webp",
  },
  film_media: {
    label: "Film & Media",
    accent: palette.rosewood,
    fallbackArtwork: "/illustrations/arts-culture.webp",
  },
  sports_games: {
    label: "Sports & Games",
    accent: palette.atlasBlue,
    fallbackArtwork: "/illustrations/places.webp",
  },
};

export function categoryPresentation(category: Category): CategoryPresentation {
  return CATEGORY_PRESENTATION[category];
}
