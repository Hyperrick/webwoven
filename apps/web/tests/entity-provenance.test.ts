import { describe, expect, it } from "vitest";
import type { EntitySummary } from "../src/lib/api/types";
import {
  provenanceFor,
  sourceMetadataFor,
  verifiedWikidataUrlFor,
  wikidataUrlFor,
} from "../src/lib/domain/entity-provenance";

function entity(
  qid: string,
  source: ReturnType<typeof sourceMetadataFor>,
): EntitySummary {
  return {
    qid,
    label: "Test entity",
    description: "Test description",
    category: "places",
    ...source,
  };
}

describe("entity source provenance", () => {
  it("creates external links only for valid Wikidata item IDs", () => {
    expect(sourceMetadataFor("Q42")).toEqual({
      source_kind: "wikidata",
      source_url: "https://www.wikidata.org/wiki/Q42",
    });
    expect(sourceMetadataFor("Q0")).toEqual({ source_kind: "unknown" });
    expect(sourceMetadataFor("not-a-qid")).toEqual({
      source_kind: "unknown",
    });
    expect(wikidataUrlFor("fixture:places:01")).toBeUndefined();
    expect(
      verifiedWikidataUrlFor({
        qid: "fixture:places:01",
        source_kind: "wikidata",
      }),
    ).toBeUndefined();
    expect(
      verifiedWikidataUrlFor({ qid: "Q42", source_kind: "synthetic_fixture" }),
    ).toBeUndefined();
  });

  it("labels fixture content as fictional project-authored test data", () => {
    const fixtureSource = sourceMetadataFor("fixture:places:01");
    const presentation = provenanceFor(
      entity("fixture:places:01", fixtureSource),
    );

    expect(fixtureSource).toEqual({ source_kind: "synthetic_fixture" });
    expect(presentation).toMatchObject({
      knowledgeSource: "Webwoven synthetic smoke fixture",
      knowledgeLicense: "MIT (project-authored fixture)",
      reviewState: "Fixture validation only",
    });
    expect(presentation.notice).toContain("not Wikidata claims");
  });

  it("preserves Wikidata and CC0 provenance for real entities", () => {
    const presentation = provenanceFor(entity("Q42", sourceMetadataFor("Q42")));

    expect(presentation).toMatchObject({
      knowledgeSource: "Wikidata structured data",
      knowledgeLicense: "CC0",
      reviewState: "Snapshot validated · editorial review pending",
    });
  });
});
