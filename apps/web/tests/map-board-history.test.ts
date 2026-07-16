import { describe, expect, it } from "vitest";
import type {
  DecisionChoice,
  DecisionConnection,
  DecisionStage,
  EntitySummary,
  SessionSnapshot,
  TrailEntry,
} from "../src/lib/api/types";
import { buildMapBoard } from "../src/lib/domain/map-board";

const start = entity("fixture:01", "Tobin Rill");
const middle = entity("fixture:02", "Paper Moon Libretto");
const influence = entity("fixture:03", "Orra Venn");
const goal = entity("fixture:04", "Sera Loom");

function entity(qid: string, label: string): EntitySummary {
  return {
    qid,
    label,
    description: `Fixture entity: ${label}.`,
    category: "art_design",
    source_kind: "synthetic_fixture",
  };
}

function choice(
  id: string,
  target: EntitySummary,
  statement: string,
  relation: Partial<DecisionChoice["relation"]> = {},
): DecisionChoice {
  return {
    id,
    target,
    relation: {
      property_id: relation.property_id ?? "P800",
      label: relation.label ?? "notable work",
      direction: relation.direction ?? "outgoing",
      glyph: relation.glyph ?? "work",
    },
    statement,
  };
}

function connection(
  id: string,
  statement: string,
  relation: Partial<DecisionConnection["relation"]> = {},
): DecisionConnection {
  return {
    id,
    relation: {
      property_id: relation.property_id ?? "P800",
      label: relation.label ?? "notable work",
      direction: relation.direction ?? "outgoing",
      glyph: relation.glyph ?? "work",
    },
    statement,
  };
}

function snapshot(
  decisionHistory: DecisionStage[],
  trail: TrailEntry[],
  current: EntitySummary,
): SessionSnapshot {
  return {
    id: "history-session",
    mode: "solo",
    category: "art_design",
    difficulty: "easy",
    started_at: "2026-07-13T10:00:00Z",
    start,
    target: goal,
    current,
    trail,
    decision_history: decisionHistory,
    moves: decisionHistory.length,
    hints_used: [],
    score: null,
    status: "active",
    state_version: decisionHistory.length,
    shortest_distance: 2,
    elapsed_seconds: 0,
    relation_groups: [],
  };
}

describe("resolved map history", () => {
  it("retains every explicit connection with one historical choice per target", () => {
    const selected = choice(
      "choice-middle",
      middle,
      "Tobin Rill wrote Paper Moon Libretto.",
    );
    selected.connections = [
      connection(
        "edge-middle-created",
        "Paper Moon Libretto was created by Tobin Rill.",
        { property_id: "P170", label: "creator of", direction: "incoming" },
      ),
      connection(
        "edge-middle-notable",
        "Tobin Rill wrote Paper Moon Libretto.",
      ),
    ];
    const discarded = choice(
      "choice-influence",
      influence,
      "Tobin Rill was influenced by Orra Venn.",
      { property_id: "P737", label: "influenced by", glyph: "influence" },
    );
    discarded.connections = [
      connection(
        "edge-influence-a",
        "Tobin Rill was influenced by Orra Venn.",
        { property_id: "P737", label: "influenced by", glyph: "influence" },
      ),
      connection(
        "edge-influence-b",
        "Orra Venn documented work by Tobin Rill.",
        { label: "documented work", direction: "incoming" },
      ),
    ];
    const stage: DecisionStage = {
      index: 0,
      source: start,
      destination: middle,
      action: "follow",
      choices: [selected, discarded],
      selected_choice_id: selected.id,
    };
    const board = buildMapBoard(
      snapshot(
        [stage],
        [
          { qid: start.qid, label: start.label },
          { qid: middle.qid, label: middle.label },
        ],
        middle,
      ),
    );
    const trailLink = board.links.find((link) => link.kind === "trail");
    const discardedNode = board.nodes.find(
      (node) => node.qid === influence.qid && node.roles.includes("discarded"),
    );
    const discardedLink = board.links.find(
      (link) => link.target_node_id === discardedNode?.id,
    );

    expect(trailLink).toMatchObject({
      action: "follow",
      statement: selected.statement,
    });
    expect(trailLink?.connections).toEqual([
      expect.objectContaining({
        id: "edge-middle-created",
        statement: "Paper Moon Libretto was created by Tobin Rill.",
        relation: expect.objectContaining({ property_id: "P170" }),
      }),
      expect.objectContaining({
        id: "edge-middle-notable",
        statement: selected.statement,
        relation: expect.objectContaining({ property_id: "P800" }),
      }),
    ]);
    expect(discardedLink?.connections?.map(({ id }) => id)).toEqual([
      "edge-influence-a",
      "edge-influence-b",
    ]);
    expect(
      board.nodes.filter(
        (node) =>
          node.qid === influence.qid && node.roles.includes("discarded"),
      ),
    ).toHaveLength(1);
    expect(
      board.links
        .flatMap((link) => link.connections ?? [])
        .every((item) => !("edge_token" in item)),
    ).toBe(true);
  });

  it("merges facts from legacy duplicate choices for a shared target", () => {
    const stage: DecisionStage = {
      index: 0,
      source: start,
      destination: middle,
      action: "follow",
      choices: [
        choice(
          "edge-middle-created",
          middle,
          "Paper Moon Libretto was created by Tobin Rill.",
          { property_id: "P170", label: "creator of", direction: "incoming" },
        ),
        choice(
          "edge-middle-notable",
          middle,
          "Tobin Rill wrote Paper Moon Libretto.",
        ),
        choice(
          "edge-influence-a",
          influence,
          "Tobin Rill was influenced by Orra Venn.",
          { property_id: "P737", label: "influenced by", glyph: "influence" },
        ),
        choice(
          "edge-influence-b",
          influence,
          "Orra Venn documented work by Tobin Rill.",
          { label: "documented work", direction: "incoming" },
        ),
      ],
      selected_choice_id: "edge-middle-notable",
    };
    const board = buildMapBoard(
      snapshot(
        [stage],
        [
          { qid: start.qid, label: start.label },
          { qid: middle.qid, label: middle.label },
        ],
        middle,
      ),
    );
    const trailLink = board.links.find((link) => link.kind === "trail");
    const discardedNode = board.nodes.find(
      (node) => node.qid === influence.qid && node.roles.includes("discarded"),
    );
    const discardedLink = board.links.find(
      (link) => link.target_node_id === discardedNode?.id,
    );

    expect(trailLink).toMatchObject({
      action: "follow",
      statement: "Tobin Rill wrote Paper Moon Libretto.",
    });
    expect(trailLink?.connections?.map(({ id }) => id)).toEqual([
      "edge-middle-created",
      "edge-middle-notable",
    ]);
    expect(discardedLink).toMatchObject({
      kind: "discarded",
      statement: "Tobin Rill was influenced by Orra Venn.",
    });
    expect(
      discardedLink?.connections?.map(({ statement }) => statement),
    ).toEqual([
      "Tobin Rill was influenced by Orra Venn.",
      "Orra Venn documented work by Tobin Rill.",
    ]);
    expect(
      discardedLink?.connections?.every(
        (connection) => !("edge_token" in connection),
      ),
    ).toBe(true);
  });

  it("rebuilds Follow and Back facts without duplicating the return option", () => {
    const followed = choice(
      "edge-middle",
      middle,
      "Tobin Rill wrote Paper Moon Libretto.",
    );
    const firstStage: DecisionStage = {
      index: 0,
      source: start,
      destination: middle,
      action: "follow",
      choices: [followed],
      selected_choice_id: followed.id,
    };
    const backStage: DecisionStage = {
      index: 1,
      source: middle,
      destination: start,
      action: "back",
      choices: [
        choice(
          "edge-return",
          start,
          "Paper Moon Libretto is a notable work of Tobin Rill.",
          { direction: "incoming" },
        ),
        choice(
          "edge-unexplored",
          influence,
          "Paper Moon Libretto was influenced by Orra Venn.",
          { property_id: "P737", label: "influenced by", glyph: "influence" },
        ),
      ],
    };
    const board = buildMapBoard(
      snapshot(
        [firstStage, backStage],
        [
          { qid: start.qid, label: start.label },
          { qid: middle.qid, label: middle.label },
          { qid: start.qid, label: start.label },
        ],
        start,
      ),
    );
    const startNodes = board.nodes.filter((node) => node.qid === start.qid);

    expect(startNodes.map(({ id }) => id)).toEqual([
      `visit:0:${start.qid}`,
      `visit:2:${start.qid}`,
    ]);
    expect(startNodes.some((node) => node.roles.includes("discarded"))).toBe(
      false,
    );
    expect(
      board.nodes.some(
        (node) =>
          node.qid === influence.qid && node.roles.includes("discarded"),
      ),
    ).toBe(true);
    expect(board.trail[1]).toMatchObject({
      action: "follow",
      statement: followed.statement,
      revisited: false,
    });
    expect(board.trail[2]).toMatchObject({
      action: "back",
      statement: "Returned to Tobin Rill.",
      revisited: true,
      connections: [],
    });
    expect(board.links.filter((link) => link.kind === "trail")).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          action: "follow",
          statement: followed.statement,
        }),
        expect.objectContaining({
          action: "back",
          statement: "Returned to Tobin Rill.",
        }),
      ]),
    );
  });
});
