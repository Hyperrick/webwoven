import { describe, expect, it } from "vitest";
import type {
  MapBoard,
  MapBoardNode,
  MapBoardNodeRole,
} from "../src/lib/domain/map-board";
import {
  mobileChoiceRowLabelLines,
  projectMobileMapBoard,
} from "../src/lib/components/map-viewport/mobile-map-board-layout";

const MOBILE_WORLD_WIDTH = 26;
const MOBILE_WORLD_CENTER = MOBILE_WORLD_WIDTH / 2;

function node(
  id: string,
  stageIndex: number,
  roles: MapBoardNodeRole[],
  y: number,
  label = id,
): MapBoardNode {
  return {
    id,
    qid: `Q-${id}`,
    label,
    roles,
    position: { x: stageIndex / 4, y, z: 0.5 },
    choice_ids: [],
    stage_index: stageIndex,
  };
}

function board(): MapBoard {
  return {
    start_node_id: "current",
    current_node_id: "current",
    goal_node_id: "goal",
    nodes: [
      node("discarded", 0, ["discarded"], 0.8),
      node("current", 0, ["start", "trail", "current"], 0.5),
      node("choice-a", 1, ["choice"], 0.2),
      node("choice-b", 1, ["choice"], 0.5),
      node("choice-c", 1, ["choice"], 0.8),
      node("goal", 2, ["goal"], 0.5),
    ],
    links: [],
    choices: [],
    trail: [],
    layout: {
      width_units: 88,
      height_units: 38,
      minimum_width_units: 88,
      minimum_height_units: 38,
      column_gap_units: 26,
      goal_gap_units: 52,
      choice_top_units: 12,
      choice_lane_gap_units: 10,
      bottom_clearance_units: 10,
      choice_lane_count: 3,
      current_column: 0,
      active_choice_column: 1,
    },
  };
}

function absolutePoint(
  projected: MapBoard,
  id: string,
): { x: number; y: number } {
  const position = projected.nodes.find(
    (candidate) => candidate.id === id,
  )?.position;
  if (!position) throw new Error(`Missing projected node ${id}`);
  return {
    x: position.x * projected.layout.width_units,
    y: position.y * projected.layout.height_units,
  };
}

describe("mobile map board layout", () => {
  it("packs active choices into deterministic two-column constellation rows", () => {
    const source = board();
    const sourceSnapshot = structuredClone(source);
    const projected = projectMobileMapBoard(source);
    const discarded = absolutePoint(projected, "discarded");
    const current = absolutePoint(projected, "current");
    const choiceA = absolutePoint(projected, "choice-a");
    const choiceB = absolutePoint(projected, "choice-b");
    const choiceC = absolutePoint(projected, "choice-c");
    const goal = absolutePoint(projected, "goal");

    expect(projected.layout).toMatchObject({
      width_units: MOBILE_WORLD_WIDTH,
      minimum_width_units: MOBILE_WORLD_WIDTH,
      minimum_height_units: 42,
    });
    expect(discarded.y).toBeLessThan(current.y);
    expect(current.x).toBeCloseTo(MOBILE_WORLD_CENTER);
    expect(current.y).toBeLessThan(choiceA.y);

    expect(choiceA.y).toBeCloseTo(choiceB.y);
    expect(choiceA.x).toBeLessThan(MOBILE_WORLD_CENTER);
    expect(choiceB.x).toBeGreaterThan(MOBILE_WORLD_CENTER);
    expect(choiceA.x + choiceB.x).toBeCloseTo(MOBILE_WORLD_WIDTH);

    expect(choiceC.y).toBeGreaterThan(choiceA.y);
    expect(choiceC.x).toBeCloseTo(MOBILE_WORLD_CENTER);
    expect(goal.y).toBeGreaterThan(choiceC.y);
    expect(goal.x).toBeCloseTo(MOBILE_WORLD_CENTER);

    expect(
      projected.nodes.every(({ position }) =>
        [position.x, position.y, position.z].every(
          (coordinate) => coordinate >= 0 && coordinate <= 1,
        ),
      ),
    ).toBe(true);
    expect(projectMobileMapBoard(source)).toEqual(projected);
    expect(projected.links).toBe(source.links);
    expect(projected.choices).toBe(source.choices);
    expect(projected.trail).toBe(source.trail);
    expect(source).toEqual(sourceSnapshot);
  });

  it("places historical and discarded nodes before the current route node", () => {
    const source = board();
    source.current_node_id = "new-current";
    source.nodes = [
      node("start", 0, ["start", "trail"], 0.5),
      node("discarded-a", 1, ["discarded"], 0.2),
      node("new-current", 1, ["trail", "current"], 0.5),
      node("discarded-b", 1, ["discarded"], 0.8),
      node("next-a", 2, ["choice"], 0.3),
      node("next-b", 2, ["choice"], 0.7),
      node("goal", 3, ["goal"], 0.5),
    ];

    const projected = projectMobileMapBoard(source);
    const current = absolutePoint(projected, "new-current");
    const discardedA = absolutePoint(projected, "discarded-a");
    const discardedB = absolutePoint(projected, "discarded-b");
    const nextA = absolutePoint(projected, "next-a");

    expect(discardedA.y).toBeLessThan(current.y);
    expect(discardedB.y).toBeLessThan(current.y);
    expect(current.x).toBeCloseTo(MOBILE_WORLD_CENTER);
    expect(current.y).toBeLessThan(nextA.y);
  });

  it("treats a reachable goal like an ordinary active choice", () => {
    const source = board();
    source.nodes = [
      node("current", 0, ["start", "trail", "current"], 0.5),
      node("goal", 1, ["choice", "goal"], 0.3),
      node("other-choice", 1, ["choice"], 0.7),
    ];
    const projected = projectMobileMapBoard(source);
    const current = absolutePoint(projected, "current");
    const goal = absolutePoint(projected, "goal");
    const otherChoice = absolutePoint(projected, "other-choice");

    expect(current.y).toBeLessThan(goal.y);
    expect(goal.y).toBeCloseTo(otherChoice.y);
    expect(goal.x).toBeLessThan(MOBILE_WORLD_CENTER);
    expect(otherChoice.x).toBeGreaterThan(MOBILE_WORLD_CENTER);
    expect(goal.x + otherChoice.x).toBeCloseTo(MOBILE_WORLD_WIDTH);
  });

  it("uses the tallest measured label for each row and expands only that row", () => {
    const source = board();
    const measuredLines = new Map([
      ["discarded", 6],
      ["choice-a", 1],
      ["choice-b", 4],
      ["choice-c", 2],
    ]);
    const rowLines = mobileChoiceRowLabelLines(source, measuredLines);
    const projected = projectMobileMapBoard(source, measuredLines);
    const choiceA = absolutePoint(projected, "choice-a");
    const choiceB = absolutePoint(projected, "choice-b");
    const choiceC = absolutePoint(projected, "choice-c");

    expect(rowLines.get("discarded")).toBe(2);
    expect(rowLines.get("choice-a")).toBe(4);
    expect(rowLines.get("choice-b")).toBe(4);
    expect(rowLines.get("choice-c")).toBe(2);
    expect(choiceA.y).toBeCloseTo(choiceB.y);
    expect(choiceC.y - choiceA.y).toBeCloseTo(7.4);
  });
});
