import { describe, expect, it } from "vitest";
import type {
  DecisionStage,
  EntitySummary,
  RelationGroup,
  SessionSnapshot,
  TrailEntry,
} from "../src/lib/api/types";
import { buildMapBoard, flattenMoveChoices } from "../src/lib/domain/map-board";

const start = entity("fixture:art_design:01", "Tobin Rill");
const middle = entity("fixture:art_design:02", "Paper Moon Libretto");
const influence = entity("fixture:art_design:03", "Orra Venn");
const target = entity("fixture:art_design:04", "Sera Loom");

function entity(qid: string, label: string): EntitySummary {
  return {
    qid,
    label,
    description: `Fictional fixture entity: ${label}.`,
    category: "art_design",
    source_kind: "synthetic_fixture",
  };
}

function group(
  propertyId: string,
  label: string,
  direction: RelationGroup["direction"],
  edges: RelationGroup["edges"],
): RelationGroup {
  return {
    group_id: `${propertyId}-${direction}-${label.replaceAll(" ", "-")}`,
    property_id: propertyId,
    label,
    direction,
    glyph: propertyId === "P737" ? "influence" : "work",
    edges,
  };
}

function snapshot(
  relationGroups: RelationGroup[],
  options: {
    current?: EntitySummary;
    trail?: TrailEntry[];
    goal?: EntitySummary;
    decisionHistory?: DecisionStage[];
  } = {},
): SessionSnapshot {
  const current = options.current ?? start;
  return {
    id: "session-1",
    mode: "solo",
    category: "art_design",
    difficulty: "easy",
    started_at: "2026-07-13T10:00:00Z",
    start,
    target: options.goal ?? target,
    current,
    trail: options.trail ?? [{ qid: current.qid, label: current.label }],
    decision_history: options.decisionHistory ?? [],
    moves: 0,
    hints_used: [],
    score: null,
    status: "active",
    state_version: 0,
    shortest_distance: 2,
    elapsed_seconds: 0,
    relation_groups: relationGroups,
  };
}

describe("deterministic map board", () => {
  it("flattens one-to-many relation groups into direct semantic choices", () => {
    const authoredStatement =
      "Tobin Rill wrote Paper Moon Libretto; it is a complete grounded fact.";
    const choices = flattenMoveChoices(
      snapshot([
        group("P800", "notable work", "outgoing", [
          {
            edge_token: "signed-middle",
            target: middle,
            statement: authoredStatement,
          },
          {
            edge_token: "signed-goal",
            target,
            statement: "Tobin Rill collaborated with Sera Loom.",
          },
        ]),
        group("P737", "influenced by", "outgoing", [
          {
            edge_token: "signed-influence",
            target: influence,
            statement: "Tobin Rill was influenced by Orra Venn.",
          },
        ]),
      ]),
    );

    expect(choices).toHaveLength(3);
    expect(choices.map((choice) => choice.target.qid)).toEqual([
      middle.qid,
      influence.qid,
      target.qid,
    ]);
    expect(choices[0]).toMatchObject({
      edge_token: "signed-middle",
      statement: authoredStatement,
      connections: [
        expect.objectContaining({
          edge_token: "signed-middle",
          statement: authoredStatement,
        }),
      ],
      relation: {
        property_id: "P800",
        label: "notable work",
        direction: "outgoing",
      },
    });
  });

  it("groups duplicate-target edges and prefers a promising primary connection", () => {
    const createdStatement = "Tobin Rill created Paper Moon Libretto.";
    const influenceStatement =
      "Paper Moon Libretto was influenced by Tobin Rill's field notes.";
    const created = group("P170", "creator of", "incoming", [
      {
        edge_token: "created-token-1",
        target: middle,
        statement: createdStatement,
      },
    ]);
    const promisingInfluence: RelationGroup = {
      ...group("P737", "influenced", "outgoing", [
        {
          edge_token: "influence-token-1",
          target: middle,
          statement: influenceStatement,
        },
      ]),
      hint: "promising",
    };
    const board = buildMapBoard(snapshot([created, promisingInfluence]));
    const choice = board.choices[0];

    expect(board.choices).toHaveLength(1);
    expect(board.nodes.filter((node) => node.qid === middle.qid)).toHaveLength(
      1,
    );
    expect(board.links.filter((link) => link.kind === "choice")).toHaveLength(
      1,
    );
    expect(choice.connections).toHaveLength(2);
    expect(
      choice.connections.map((connection) => ({
        token: connection.edge_token,
        relation: connection.relation.label,
        statement: connection.statement,
      })),
    ).toEqual([
      {
        token: "created-token-1",
        relation: "creator of",
        statement: createdStatement,
      },
      {
        token: "influence-token-1",
        relation: "influenced",
        statement: influenceStatement,
      },
    ]);
    expect(choice).toMatchObject({
      edge_token: "influence-token-1",
      relation: { hint: "promising", property_id: "P737" },
      statement: influenceStatement,
    });
    expect(choice.primary_connection_id).toBe(choice.connections[1].id);

    const refreshed = buildMapBoard(
      snapshot([
        {
          ...promisingInfluence,
          edges: [
            {
              ...promisingInfluence.edges[0],
              edge_token: "random-influence-token-2",
            },
          ],
        },
        {
          ...created,
          edges: [
            {
              ...created.edges[0],
              edge_token: "random-created-token-2",
            },
          ],
        },
      ]),
    );
    const originalTargetNode = board.nodes.find(
      (node) => node.qid === middle.qid,
    );
    const refreshedTargetNode = refreshed.nodes.find(
      (node) => node.qid === middle.qid,
    );

    expect(refreshed.choices[0].id).toBe(choice.id);
    expect(refreshed.choices[0].connections.map(({ id }) => id)).toEqual(
      choice.connections.map(({ id }) => id),
    );
    expect(refreshedTargetNode?.position).toEqual(originalTargetNode?.position);
  });

  it("keeps ordering, stable ids, and layout independent of signed tokens", () => {
    const originalGroups = [
      group("P800", "notable work", "outgoing", [
        {
          edge_token: "token-a-1",
          target,
          statement: "Tobin Rill collaborated with Sera Loom.",
        },
        {
          edge_token: "token-b-1",
          target: middle,
          statement: "Tobin Rill wrote Paper Moon Libretto.",
        },
      ]),
      group("P737", "influenced by", "outgoing", [
        {
          edge_token: "token-c-1",
          target: influence,
          statement: "Tobin Rill was influenced by Orra Venn.",
        },
      ]),
    ];
    const refreshedGroups = [
      group("P737", "influenced by", "outgoing", [
        {
          edge_token: "random-token-c-2",
          target: influence,
          statement: "Tobin Rill was influenced by Orra Venn.",
        },
      ]),
      group("P800", "notable work", "outgoing", [
        {
          edge_token: "random-token-b-2",
          target: middle,
          statement: "Tobin Rill wrote Paper Moon Libretto.",
        },
        {
          edge_token: "random-token-a-2",
          target,
          statement: "Tobin Rill collaborated with Sera Loom.",
        },
      ]),
    ];
    const original = buildMapBoard(snapshot(originalGroups));
    const refreshed = buildMapBoard(snapshot(refreshedGroups));

    expect(
      refreshed.choices.map(({ id, target: item }) => [id, item.qid]),
    ).toEqual(original.choices.map(({ id, target: item }) => [id, item.qid]));
    expect(refreshed.choices.map((choice) => choice.edge_token)).not.toEqual(
      original.choices.map((choice) => choice.edge_token),
    );
    expect(
      refreshed.nodes.map(({ qid, position }) => ({ qid, position })),
    ).toEqual(original.nodes.map(({ qid, position }) => ({ qid, position })));
  });

  it("represents a reachable goal once with both choice and goal roles", () => {
    const board = buildMapBoard(
      snapshot([
        group("P800", "collaborated with", "outgoing", [
          {
            edge_token: "signed-goal",
            target,
            statement: "Tobin Rill collaborated with Sera Loom.",
          },
        ]),
      ]),
    );
    const goalNodes = board.nodes.filter((node) => node.qid === target.qid);
    const currentNode = board.nodes.find(
      (node) => node.id === board.current_node_id,
    );

    expect(goalNodes).toHaveLength(1);
    expect(goalNodes[0].roles).toEqual(["choice", "goal"]);
    expect(goalNodes[0].choice_ids).toEqual([board.choices[0].id]);
    expect(board.goal_node_id).toBe(board.choices[0].target_node_id);
    expect(currentNode?.roles).toEqual(["start", "trail", "current"]);
  });

  it("clusters ordinary nodes and reserves a wider gap for a distant goal", () => {
    const board = buildMapBoard(
      snapshot([
        group("P800", "notable work", "outgoing", [
          {
            edge_token: "signed-middle",
            target: middle,
            statement: "Tobin Rill wrote Paper Moon Libretto.",
          },
        ]),
      ]),
    );
    const choiceNode = board.nodes.find(
      (node) => node.id === board.choices[0]?.target_node_id,
    );
    const goalNode = board.nodes.find((node) => node.id === board.goal_node_id);
    const currentNode = board.nodes.find(
      (node) => node.id === board.current_node_id,
    );
    const currentToChoiceGap =
      ((choiceNode?.position.x ?? 0) - (currentNode?.position.x ?? 0)) *
      board.layout.width_units;
    const choiceToGoalGap =
      ((goalNode?.position.x ?? 0) - (choiceNode?.position.x ?? 0)) *
      board.layout.width_units;

    expect(board.layout.column_gap_units).toBe(26);
    expect(board.layout.goal_gap_units).toBe(52);
    expect(currentToChoiceGap).toBeCloseTo(26);
    expect(choiceToGoalGap).toBeCloseTo(52);
    expect(choiceToGoalGap).toBeGreaterThan(currentToChoiceGap);
  });

  it("uses fixed vertical lanes for every onward choice", () => {
    const destinations = Array.from({ length: 9 }, (_, index) =>
      entity(
        `fixture:places_architecture:${String(index + 1).padStart(2, "0")}`,
        `Map marker ${index + 1}`,
      ),
    );
    const board = buildMapBoard(
      snapshot([
        group("P361", "connected with", "outgoing", [
          ...destinations.map((destination, index) => ({
            edge_token: `destination-token-${index}`,
            target: destination,
            statement: `Tobin Rill is connected with ${destination.label}.`,
          })),
          {
            edge_token: "goal-token",
            target,
            statement: "Tobin Rill is connected with Sera Loom.",
          },
        ]),
      ]),
    );
    const nodesById = new Map(board.nodes.map((node) => [node.id, node]));
    const choiceNodes = board.choices.map((choice) =>
      nodesById.get(choice.target_node_id),
    );
    const absoluteY = choiceNodes.map(
      (node) => (node?.position.y ?? 0) * board.layout.height_units,
    );
    const goalNode = nodesById.get(board.goal_node_id);

    expect(board.choices).toHaveLength(10);
    expect(board.layout).toMatchObject({
      height_units: 112,
      choice_top_units: 12,
      choice_lane_gap_units: 10,
      choice_lane_count: 10,
    });
    expect(absoluteY[0]).toBeCloseTo(12);
    for (let index = 1; index < absoluteY.length; index += 1) {
      expect(absoluteY[index] - absoluteY[index - 1]).toBeCloseTo(10);
    }
    expect(absoluteY).toContain(
      (goalNode?.position.y ?? 0) * board.layout.height_units,
    );
    expect(goalNode?.roles).toEqual(["choice", "goal"]);
    expect(
      board.nodes.every(({ position }) =>
        [position.x, position.y, position.z].every(
          (coordinate) => coordinate >= 0 && coordinate <= 1,
        ),
      ),
    ).toBe(true);
  });

  it("exposes chronological trail links and normalized positions", () => {
    const pastStatement = "Tobin Rill wrote Paper Moon Libretto.";
    const nextStatement = "Paper Moon Libretto credits Sera Loom.";
    const board = buildMapBoard(
      snapshot(
        [
          group("P800", "credits", "outgoing", [
            {
              edge_token: "next-token",
              target,
              statement: nextStatement,
            },
          ]),
        ],
        {
          current: middle,
          trail: [
            { qid: start.qid, label: start.label },
            {
              qid: middle.qid,
              label: middle.label,
              relation: pastStatement,
            },
          ],
        },
      ),
    );

    expect(board.trail.map((visit) => visit.qid)).toEqual([
      start.qid,
      middle.qid,
    ]);
    expect(board.links).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ kind: "trail", statement: pastStatement }),
        expect.objectContaining({ kind: "choice", statement: nextStatement }),
      ]),
    );
    expect(
      board.nodes.every(({ position }) =>
        [position.x, position.y, position.z].every(
          (coordinate) => coordinate >= 0 && coordinate <= 1,
        ),
      ),
    ).toBe(true);
  });

  it("freezes rejected routes and widens after a followed decision", () => {
    const firstGroups = [
      group("P800", "notable work", "outgoing", [
        {
          edge_token: "signed-middle",
          target: middle,
          statement: "Tobin Rill wrote Paper Moon Libretto.",
        },
      ]),
      group("P737", "influenced by", "outgoing", [
        {
          edge_token: "signed-influence",
          target: influence,
          statement: "Tobin Rill was influenced by Orra Venn.",
        },
      ]),
    ];
    const initial = buildMapBoard(snapshot(firstGroups));
    const stage: DecisionStage = {
      index: 0,
      source: start,
      destination: middle,
      action: "follow",
      choices: [
        {
          id: "edge-middle",
          target: middle,
          relation: {
            property_id: "P800",
            label: "notable work",
            direction: "outgoing",
            glyph: "work",
          },
          statement: "Tobin Rill wrote Paper Moon Libretto.",
        },
        {
          id: "edge-influence",
          target: influence,
          relation: {
            property_id: "P737",
            label: "influenced by",
            direction: "outgoing",
            glyph: "influence",
          },
          statement: "Tobin Rill was influenced by Orra Venn.",
        },
      ],
      selected_choice_id: "edge-middle",
    };
    const widened = buildMapBoard(
      snapshot(
        [
          group("P800", "credits", "outgoing", [
            {
              edge_token: "signed-target",
              target,
              statement: "Paper Moon Libretto credits Sera Loom.",
            },
          ]),
        ],
        {
          current: middle,
          trail: [
            { qid: start.qid, label: start.label },
            { qid: middle.qid, label: middle.label },
          ],
          decisionHistory: [stage],
        },
      ),
    );
    const initialMiddle = initial.nodes.find((node) => node.qid === middle.qid);
    const selectedMiddle = widened.nodes.find(
      (node) => node.qid === middle.qid && node.roles.includes("current"),
    );
    const rejectedInfluence = widened.nodes.find(
      (node) => node.qid === influence.qid,
    );

    expect(widened.layout.width_units).toBeGreaterThan(
      initial.layout.width_units,
    );
    expect(selectedMiddle?.roles).toEqual(["trail", "current"]);
    expect(rejectedInfluence?.roles).toEqual(["discarded"]);
    expect(rejectedInfluence?.choice_ids).toEqual([
      "history-choice:0:fixture:art_design:03",
    ]);
    expect(
      (selectedMiddle?.position.x ?? 0) * widened.layout.width_units,
    ).toBeCloseTo(
      (initialMiddle?.position.x ?? 0) * initial.layout.width_units,
    );
    expect(widened.links.some((link) => link.kind === "discarded")).toBe(true);
    expect(
      widened.choices.every((choice) => choice.edge_token.length > 0),
    ).toBe(true);
  });
});
