import type { EntitySummary } from "../api/types";
import { categoryPresentation } from "./categories";

export type EndpointArtworkKind = "commons" | "category";

export interface EndpointArtwork {
  src: string;
  kind: EndpointArtworkKind;
}

/**
 * Prefer verified documentary media and use an authored category plate only
 * when an endpoint has no accepted Commons image.
 */
export function endpointArtworkFor(entity: EntitySummary): EndpointArtwork {
  return entity.image_path
    ? { src: entity.image_path, kind: "commons" }
    : {
        src: categoryPresentation(entity.category).fallbackArtwork,
        kind: "category",
      };
}
