import { describe, expect, it } from "vitest";
import {
  createNavigationState,
  followEdge,
  moveBack,
} from "../src/lib/domain/navigation";
import { buildMapBoard } from "../src/lib/domain/map-board";
import { deriveMapTransition } from "../src/lib/domain/map-transition";

describe("map transitions", () => {
  it("collapses a dead-end retreat without moving the original node", () => {
    const initial = createNavigationState("transition", "solo");
    const followed = followEdge(initial, "demo:Q5586:P800:Q209772");
    const backed = moveBack(followed);
    const previousBoard = buildMapBoard(followed.snapshot);
    const nextBoard = buildMapBoard(backed.snapshot);
    const transition = deriveMapTransition(
      followed.snapshot,
      backed.snapshot,
      previousBoard,
      nextBoard,
    );

    expect(transition).toMatchObject({
      kind: "dead_end_back",
      from_node_id: previousBoard.current_node_id,
      to_node_id: nextBoard.current_node_id,
    });
    expect(
      nextBoard.nodes.find(({ id }) => id === transition.from_node_id),
    ).toBeUndefined();
    expect(
      nextBoard.nodes.find(({ id }) => id === nextBoard.current_node_id)
        ?.position,
    ).toEqual(
      previousBoard.nodes.find(({ id }) => id === previousBoard.start_node_id)
        ?.position,
    );
    expect(nextBoard.layout.width_units).toBe(previousBoard.layout.width_units);
    expect(nextBoard.trail).toHaveLength(3);
  });
});
