import type { Category, EntitySummary } from "../api/types";

export type EndpointArtworkKind = "commons" | "category";

export interface EndpointArtwork {
  src: string;
  kind: EndpointArtworkKind;
}

const CATEGORY_ARTWORK: Record<Category, string> = {
  history_people: "/illustrations/history-people.webp",
  nature_science: "/illustrations/nature-science.webp",
  arts_culture: "/illustrations/arts-culture.webp",
  places: "/illustrations/places.webp",
};

/**
 * Prefer verified documentary media and use an authored category plate only
 * when an endpoint has no accepted Commons image.
 */
export function endpointArtworkFor(entity: EntitySummary): EndpointArtwork {
  return entity.image_path
    ? { src: entity.image_path, kind: "commons" }
    : { src: CATEGORY_ARTWORK[entity.category], kind: "category" };
}
