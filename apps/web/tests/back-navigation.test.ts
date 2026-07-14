import { describe, expect, it } from "vitest";
import type { EntitySummary, SessionStatus } from "../src/lib/api/types";
import { activeBackDestination } from "../src/lib/domain/back-navigation";

function entity(qid: string): EntitySummary {
  return {
    qid,
    label: `Entity ${qid}`,
    description: "Fixture entity",
    category: "places",
    source_kind: "synthetic_fixture",
  };
}

function session(status: SessionStatus, stack?: EntitySummary[]) {
  return { status, navigation_stack: stack };
}

describe("active Back destination", () => {
  it("uses the mutable server stack rather than chronological trail order", () => {
    const start = entity("Q1");
    const current = entity("Q2");

    expect(activeBackDestination(session("active", [start, current]))).toBe(
      start,
    );
  });

  it("offers no Back action at the start or outside an active round", () => {
    const start = entity("Q1");
    const current = entity("Q2");

    expect(activeBackDestination(session("active", [start]))).toBeUndefined();
    expect(
      activeBackDestination(session("completed", [start, current])),
    ).toBeUndefined();
    expect(activeBackDestination(session("active"))).toBeUndefined();
  });
});
