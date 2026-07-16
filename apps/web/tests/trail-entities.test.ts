import { describe, expect, it } from "vitest";
import type { EntitySummary, SessionSnapshot } from "../src/lib/api/types";
import {
  sessionMediaEntities,
  trailEntityAt,
} from "../src/lib/domain/trail-entities";

function entity(qid: string): EntitySummary {
  return {
    qid,
    label: qid,
    description: `${qid} description`,
    category: "art_design",
    source_kind: "wikidata",
    image_path: `/api/v1/media/${qid}.jpg`,
  };
}

function snapshot(): SessionSnapshot {
  const start = entity("Q1");
  const middle = entity("Q2");
  const target = entity("Q3");
  return {
    id: "session",
    mode: "solo",
    category: "art_design",
    difficulty: "normal",
    started_at: "2026-07-15T12:00:00Z",
    start,
    target,
    current: target,
    trail: [
      { qid: "Q1", label: "Q1", summary: start },
      { qid: "Q2", label: "Q2", summary: middle },
      { qid: "Q3", label: "Q3", summary: target },
    ],
    navigation_stack: [start, middle, target],
    decision_history: [],
    moves: 2,
    hints_used: [],
    score: 1000,
    status: "completed",
    state_version: 2,
    shortest_distance: 2,
    elapsed_seconds: 20,
    relation_groups: [],
  };
}

describe("trail entities", () => {
  it("returns the complete summary for every route node", () => {
    const session = snapshot();

    expect(
      session.trail.map((_, index) => trailEntityAt(session, index)?.qid),
    ).toEqual(["Q1", "Q2", "Q3"]);
  });

  it("deduplicates every entity whose artwork may be visible", () => {
    expect(sessionMediaEntities(snapshot()).map((item) => item.qid)).toEqual([
      "Q1",
      "Q3",
      "Q2",
    ]);
  });
});
