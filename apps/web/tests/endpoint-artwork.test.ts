import { describe, expect, it } from "vitest";
import type { Category, EntitySummary } from "../src/lib/api/types";
import { endpointArtworkFor } from "../src/lib/domain/endpoint-artwork";

const entity = (category: Category): EntitySummary => ({
  qid: "Q1",
  label: "Example endpoint",
  description: "A test endpoint.",
  category,
  source_kind: "wikidata",
});

describe("endpoint artwork", () => {
  it("prefers an accepted local Commons image", () => {
    expect(
      endpointArtworkFor({
        ...entity("art_design"),
        image_path: "/api/v1/media/verified.jpg",
      }),
    ).toEqual({
      src: "/api/v1/media/verified.jpg",
      kind: "commons",
    });
  });

  it.each([
    ["people", "/illustrations/history-people.webp"],
    ["history_society", "/illustrations/history-people.webp"],
    ["science_technology", "/illustrations/nature-science.webp"],
    ["nature_life", "/illustrations/nature-science.webp"],
    ["art_design", "/illustrations/arts-culture.webp"],
    ["places_architecture", "/illustrations/places.webp"],
    ["literature_language", "/illustrations/arts-culture.webp"],
    ["music_performance", "/illustrations/arts-culture.webp"],
    ["film_media", "/illustrations/arts-culture.webp"],
    ["sports_games", "/illustrations/places.webp"],
  ] as const)(
    "uses the authored %s category plate as fallback",
    (category, src) => {
      expect(endpointArtworkFor(entity(category))).toEqual({
        src,
        kind: "category",
      });
    },
  );
});
