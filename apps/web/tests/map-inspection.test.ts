import { describe, expect, it } from "vitest";
import type {
  MapBoard,
  MapBoardLink,
  MapBoardNode,
} from "../src/lib/domain/map-board";
import {
  inspectMapNode,
  isInspectableMapNode,
} from "../src/lib/domain/map-inspection";

function node(
  id: string,
  label: string,
  roles: MapBoardNode["roles"],
  description = `${label} description.`,
): MapBoardNode {
  return {
    id,
    qid: `Q-${id}`,
    label,
    summary: {
      qid: `Q-${id}`,
      label,
      description,
      category: "arts_culture",
      source_kind: "wikidata",
    },
    roles,
    position: { x: 0.5, y: 0.5, z: 0.5 },
    choice_ids: [],
    stage_index: 0,
  };
}

function board(nodes: MapBoardNode[], links: MapBoardLink[] = []): MapBoard {
  return {
    start_node_id: nodes[0]?.id ?? "missing",
    current_node_id:
      nodes.find((candidate) => candidate.roles.includes("current"))?.id ??
      nodes[0]?.id ??
      "missing",
    goal_node_id: "goal",
    nodes,
    links,
    choices: [],
    trail: [],
    layout: {
      width_units: 88,
      height_units: 38,
      minimum_width_units: 88,
      minimum_height_units: 38,
      column_gap_units: 26,
      choice_top_units: 12,
      choice_lane_gap_units: 7.5,
      bottom_clearance_units: 10,
      choice_lane_count: 0,
      current_column: 1,
      active_choice_column: 2,
    },
  };
}

describe("map node inspection", () => {
  it("shows the source, target, description, and every stored statement", () => {
    const source = node("start", "Hokusai", ["start", "trail"]);
    const target = node("visit-1", "The Great Wave", ["trail"]);
    const map = board(
      [source, target],
      [
        {
          id: "trail-link",
          kind: "trail",
          source_node_id: source.id,
          target_node_id: target.id,
          statement: "Hokusai created The Great Wave.",
          connections: [
            {
              id: "created-work",
              relation: {
                group_id: "P800-outgoing",
                property_id: "P800",
                label: "notable work",
                direction: "outgoing",
                glyph: "work",
              },
              statement: "Hokusai created The Great Wave.",
            },
            {
              id: "work-by",
              relation: {
                group_id: "P170-incoming",
                property_id: "P170",
                label: "creator",
                direction: "incoming",
                glyph: "work",
              },
              statement: "The Great Wave is a work by Hokusai.",
            },
          ],
        },
      ],
    );

    expect(inspectMapNode(map, target.id)).toEqual({
      node_id: target.id,
      qid: target.qid,
      label: target.label,
      artwork: target.summary,
      description: "The Great Wave description.",
      status: "taken",
      connections: [
        {
          link_id: "trail-link",
          kind: "trail",
          source: {
            node_id: source.id,
            qid: source.qid,
            label: source.label,
          },
          target: {
            node_id: target.id,
            qid: target.qid,
            label: target.label,
          },
          statements: [
            "Hokusai created The Great Wave.",
            "The Great Wave is a work by Hokusai.",
          ],
        },
      ],
    });
  });

  it("marks rejected historical options as not taken", () => {
    const source = node("start", "Hokusai", ["start", "trail"]);
    const rejected = node("rejected", "Another work", ["discarded"]);
    const map = board(
      [source, rejected],
      [
        {
          id: "discarded-link",
          kind: "discarded",
          source_node_id: source.id,
          target_node_id: rejected.id,
          statement: "Hokusai created Another work.",
        },
      ],
    );

    expect(inspectMapNode(map, rejected.id)).toMatchObject({
      status: "not_taken",
      description: "Another work description.",
      connections: [
        {
          source: { label: "Hokusai" },
          target: { label: "Another work" },
          statements: ["Hokusai created Another work."],
        },
      ],
    });
  });

  it("gives current precedence and keeps the route start honest", () => {
    const current = node("start", "Hokusai", ["start", "trail", "current"], "");
    const map = board([current]);

    expect(inspectMapNode(map, current.id)).toMatchObject({
      status: "current",
      description: "No description is available in this graph snapshot.",
      connections: [],
    });
  });

  it("does not turn live route choices into inspection targets", () => {
    const choice = node("choice", "Next entity", ["choice"]);
    const map = board([choice]);

    expect(isInspectableMapNode(choice)).toBe(false);
    expect(inspectMapNode(map, choice.id)).toBeUndefined();
  });
});
