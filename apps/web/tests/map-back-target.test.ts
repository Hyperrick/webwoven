import { describe, expect, it } from "vitest";
import type { MapBoardLink } from "../src/lib/domain/map-board";
import { mapBackTargetNodeId } from "../src/lib/domain/map-back-target";

function link(
  kind: MapBoardLink["kind"],
  source: string,
  target: string,
): MapBoardLink {
  return {
    id: `${kind}:${source}:${target}`,
    kind,
    source_node_id: source,
    target_node_id: target,
  };
}

describe("map Back target", () => {
  it("returns the trail node connected directly into the current node", () => {
    expect(
      mapBackTargetNodeId({
        current_node_id: "current",
        links: [
          link("trail", "start", "previous"),
          link("trail", "previous", "current"),
        ],
      }),
    ).toBe("previous");
  });

  it("ignores non-trail links into the current node", () => {
    expect(
      mapBackTargetNodeId({
        current_node_id: "current",
        links: [
          link("discarded", "discarded", "current"),
          link("choice", "choice", "current"),
        ],
      }),
    ).toBeNull();
  });

  it("returns no target at the beginning of an active route", () => {
    expect(
      mapBackTargetNodeId({ current_node_id: "start", links: [] }),
    ).toBeNull();
  });
});
