import { describe, expect, it } from "vitest";
import type { EntitySummary } from "../src/lib/api/types";
import {
  imageAttributionFor,
  imageAttributionsFor,
} from "../src/lib/domain/image-attribution";

const entity: EntitySummary = {
  qid: "Q1",
  label: "The Great Wave",
  description: "woodblock print by Hokusai",
  category: "arts_culture",
  source_kind: "wikidata",
  image_attribution: {
    file_name: "The Great Wave off Kanagawa.jpg",
    original_url: "https://upload.wikimedia.org/original.jpg",
    derivative_url: "https://upload.wikimedia.org/thumbnail.jpg",
    source_url: "https://commons.wikimedia.org/wiki/File:The_Great_Wave.jpg",
    license_id: "PUBLIC_DOMAIN",
    creator: "Katsushika Hokusai",
    license_url: "https://creativecommons.org/publicdomain/mark/1.0/",
    attribution_text: "Katsushika Hokusai — Public Domain — Wikimedia Commons",
  },
};

describe("image attribution presentation", () => {
  it("provides concise creator, source, and license links", () => {
    expect(imageAttributionFor(entity)).toEqual({
      creator: "Katsushika Hokusai",
      fileName: "The Great Wave off Kanagawa.jpg",
      sourceUrl: "https://commons.wikimedia.org/wiki/File:The_Great_Wave.jpg",
      licenseLabel: "Public domain",
      licenseUrl: "https://creativecommons.org/publicdomain/mark/1.0/",
      attributionText: "Katsushika Hokusai — Public Domain — Wikimedia Commons",
    });
  });

  it("omits the credit block when an entity has no image attribution", () => {
    expect(
      imageAttributionFor({ ...entity, image_attribution: undefined }),
    ).toBe(undefined);
  });

  it("credits every distinct image used by the round", () => {
    const target = {
      ...entity,
      qid: "Q2",
      label: "British Museum",
      image_attribution: {
        ...entity.image_attribution!,
        file_name: "British Museum.jpg",
        source_url:
          "https://commons.wikimedia.org/wiki/File:British_Museum.jpg",
        creator: "Example photographer",
      },
    };

    expect(imageAttributionsFor([entity, target, entity])).toEqual([
      expect.objectContaining({ entityLabel: "The Great Wave" }),
      expect.objectContaining({ entityLabel: "British Museum" }),
    ]);
  });
});
