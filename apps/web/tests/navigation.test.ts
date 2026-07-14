import { describe, expect, it } from "vitest";
import {
  createNavigationState,
  followEdge,
  moveBack,
  useHint,
} from "../src/lib/domain/navigation";

describe("demo navigation", () => {
  it("keeps an immutable visible trail while Back changes the active stack", () => {
    const initial = createNavigationState("session", "solo");
    const wave = followEdge(initial, "demo:Q5586:P800:Q149116");
    const returned = moveBack(wave);

    expect(initial.snapshot.difficulty).toBe("normal");
    expect(initial.snapshot.current.qid).toBe("Q5586");
    expect(returned.snapshot.current.qid).toBe("Q5586");
    expect(returned.stack).toEqual(["Q5586"]);
    expect(returned.snapshot.moves).toBe(2);
    expect(returned.snapshot.trail.map((item) => item.qid)).toEqual([
      "Q5586",
      "Q149116",
      "Q5586",
    ]);
    expect(returned.snapshot.trail.at(-1)?.revisited).toBe(true);
    expect(
      returned.snapshot.relation_groups.flatMap((group) =>
        group.edges.map((edge) => edge.target.qid),
      ),
    ).toContain("Q149116");
  });

  it("removes reverse connections to entities already visited", () => {
    const initial = createNavigationState("session", "solo");
    const series = followEdge(initial, "demo:Q5586:P800:Q209772");
    const targets = series.snapshot.relation_groups.flatMap((group) =>
      group.edges.map((edge) => edge.target.qid),
    );

    expect(targets).not.toContain("Q5586");
    expect(() => followEdge(series, "demo:Q209772:P170:Q5586")).toThrow(
      "already in your active route",
    );
    expect(series.snapshot.moves).toBe(1);
  });

  it("completes only when the target entity is reached", () => {
    let state = createNavigationState("session", "daily");
    for (const edge of [
      "demo:Q5586:P800:Q149116",
      "demo:Q149116:P276:Q6373",
      "demo:Q6373:P131:Q84",
      "demo:Q84:P17:Q145",
    ]) {
      state = followEdge(state, edge);
    }

    expect(state.snapshot.status).toBe("completed");
    expect(state.snapshot.moves).toBe(4);
    expect(state.snapshot.current.qid).toBe(state.snapshot.target.qid);
    expect(state.snapshot.score).toBeGreaterThan(0);
  });

  it("applies each hint once through the dedicated hint policy", () => {
    const initial = createNavigationState("session", "solo");
    const hinted = useHint(initial, "lens");
    expect(hinted.snapshot.hints_used).toHaveLength(1);
    expect(hinted.snapshot.hints_used[0].penalty).toBe(150);
    expect(
      hinted.snapshot.relation_groups.some(
        (group) => group.hint === "promising",
      ),
    ).toBe(true);
  });
});
