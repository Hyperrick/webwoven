import type { EntitySourceKind, EntitySummary } from "../api/types";

const WIKIDATA_ITEM_ID = /^Q[1-9]\d*$/;
const FIXTURE_ID_PREFIX = "fixture:";

interface EntitySourceMetadata {
  source_kind: EntitySourceKind;
  source_url?: string;
}

export interface ProvenancePresentation {
  entityIndexLabel: string;
  knowledgeSource: string;
  knowledgeLicense: string;
  reviewState: string;
  notice?: string;
}

export function wikidataUrlFor(qid: string): string | undefined {
  return WIKIDATA_ITEM_ID.test(qid)
    ? `https://www.wikidata.org/wiki/${qid}`
    : undefined;
}

export function verifiedWikidataUrlFor(
  entity: Pick<EntitySummary, "qid" | "source_kind">,
): string | undefined {
  return entity.source_kind === "wikidata"
    ? wikidataUrlFor(entity.qid)
    : undefined;
}

export function sourceMetadataFor(qid: string): EntitySourceMetadata {
  const wikidataUrl = wikidataUrlFor(qid);
  if (wikidataUrl) {
    return {
      source_kind: "wikidata",
      source_url: wikidataUrl,
    };
  }
  if (qid.startsWith(FIXTURE_ID_PREFIX)) {
    return { source_kind: "synthetic_fixture" };
  }
  return { source_kind: "unknown" };
}

export function provenanceFor(entity?: EntitySummary): ProvenancePresentation {
  if (!entity) {
    return {
      entityIndexLabel: "Open knowledge",
      knowledgeSource: "Build attribution manifest",
      knowledgeLicense: "Varies by graph build",
      reviewState: "Build-specific",
    };
  }

  if (entity.source_kind === "wikidata") {
    return {
      entityIndexLabel: `Current entity · ${entity.qid}`,
      knowledgeSource: "Wikidata structured data",
      knowledgeLicense: "CC0",
      reviewState: "Snapshot validated · editorial review pending",
    };
  }

  if (entity.source_kind === "synthetic_fixture") {
    return {
      entityIndexLabel: `Synthetic test entity · ${entity.qid}`,
      knowledgeSource: "Webwoven synthetic smoke fixture",
      knowledgeLicense: "MIT (project-authored fixture)",
      reviewState: "Fixture validation only",
      notice:
        "This fictional entity and its connections were authored for local testing. They are not Wikidata claims.",
    };
  }

  return {
    entityIndexLabel: `Local entity · ${entity.qid}`,
    knowledgeSource: "Unidentified local graph data",
    knowledgeLicense: "See the graph attribution manifest",
    reviewState: "Source type not verified",
    notice: "No verified external source record is available for this entity.",
  };
}
