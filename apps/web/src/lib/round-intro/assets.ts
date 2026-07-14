import { palette } from "@webwoven/design-tokens/tokens";
import type { Category } from "../api/types";

interface CategoryArtwork {
  label: string;
  image: string;
  accent: string;
}

const CATEGORY_ARTWORK: Record<Category, CategoryArtwork> = {
  history_people: {
    label: "History & People",
    image: "/illustrations/history-people.webp",
    accent: palette.ochre,
  },
  nature_science: {
    label: "Nature & Science",
    image: "/illustrations/nature-science.webp",
    accent: palette.moss,
  },
  arts_culture: {
    label: "Arts & Culture",
    image: "/illustrations/arts-culture.webp",
    accent: palette.signal,
  },
  places: {
    label: "Places",
    image: "/illustrations/places.webp",
    accent: palette.cartographic,
  },
};

export function categoryArtwork(category: Category): CategoryArtwork {
  return CATEGORY_ARTWORK[category];
}

export function preloadCategoryArtwork(): void {
  for (const artwork of Object.values(CATEGORY_ARTWORK)) {
    const image = new Image();
    image.decoding = "async";
    image.src = artwork.image;
  }
}
