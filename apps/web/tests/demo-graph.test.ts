import { describe, expect, it } from "vitest";

import { DEMO_EDGES, relationGroupsFor } from "../src/lib/domain/demo-graph";

describe("browser demo relationship data", () => {
  it("stores complete authored statements for every edge", () => {
    const edges = Object.values(DEMO_EDGES).flat();

    expect(edges.length).toBeGreaterThan(0);
    expect(edges.every((edge) => /[.!?]$/.test(edge.statement))).toBe(true);
    expect(edges.every((edge) => !/[\r\n]/.test(edge.statement))).toBe(true);
  });

  it("keeps relation direction and wording aligned for the public demo route", () => {
    const pacificGroups = relationGroupsFor("Q98");
    const japan = pacificGroups
      .flatMap((group) => group.edges.map((edge) => ({ group, edge })))
      .find(({ edge }) => edge.target.qid === "Q17");
    const hokusai = relationGroupsFor("Q5586").flatMap((group) => group.edges);
    const london = relationGroupsFor("Q84").flatMap((group) => group.edges);

    expect(japan?.group).toMatchObject({
      property_id: "P276",
      direction: "incoming",
    });
    expect(japan?.edge.statement).toBe(
      "Japan is located along the western Pacific Ocean.",
    );
    expect(hokusai[0]?.statement).toBe(
      "The Great Wave off Kanagawa is a notable work by Hokusai.",
    );
    expect(london[0]?.statement).toBe("London is in the United Kingdom.");
  });
});
