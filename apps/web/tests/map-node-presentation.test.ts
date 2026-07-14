import { describe, expect, it } from "vitest";
import type {
  MapBoardNode,
  MapBoardNodeRole,
} from "../src/lib/domain/map-board";
import { mapNodeTokenPresentation } from "../src/lib/components/map-node-presentation";

function node(...roles: MapBoardNodeRole[]): MapBoardNode {
  return {
    id: roles.join(":"),
    qid: "Q1",
    label: "Map node",
    roles,
    position: { x: 0.5, y: 0.5, z: 0.5 },
    choice_ids: [],
    stage_index: 0,
  };
}

describe("map node token presentation", () => {
  it("lets an ordinary live choice card own its endpoint", () => {
    expect(mapNodeTokenPresentation(node("choice"))).toBeNull();
  });

  it("keeps one typed state and radius contract for both renderers", () => {
    expect(mapNodeTokenPresentation(node())).toEqual({
      state: "discarded",
      radius: 15,
    });
    expect(mapNodeTokenPresentation(node("choice", "goal"))).toEqual({
      state: "goal",
      radius: 20,
    });
    expect(mapNodeTokenPresentation(node("trail", "current"))).toEqual({
      state: "current",
      radius: 23,
    });
    expect(mapNodeTokenPresentation(node("trail"))).toEqual({
      state: "trail",
      radius: 17.5,
    });
    expect(mapNodeTokenPresentation(node("discarded", "goal"))).toEqual({
      state: "discarded",
      radius: 15,
    });
  });
});
