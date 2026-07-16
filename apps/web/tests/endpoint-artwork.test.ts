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
        ...entity("arts_culture"),
        image_path: "/api/v1/media/verified.jpg",
      }),
    ).toEqual({
      src: "/api/v1/media/verified.jpg",
      kind: "commons",
    });
  });

  it.each([
    ["history_people", "/illustrations/history-people.webp"],
    ["nature_science", "/illustrations/nature-science.webp"],
    ["arts_culture", "/illustrations/arts-culture.webp"],
    ["places", "/illustrations/places.webp"],
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
