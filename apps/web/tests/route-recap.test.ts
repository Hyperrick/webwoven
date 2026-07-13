import { describe, expect, it } from "vitest";
import type { SessionSnapshot } from "../src/lib/api/types";
import { routeRecap } from "../src/lib/domain/route-recap";

const entity = (qid: string, label: string) => ({
  qid,
  label,
  description: `${label} description`,
  category: "arts_culture" as const,
  source_kind: "synthetic_fixture" as const,
});

describe("route recap", () => {
  it("uses only the completed route instead of unrelated static copy", () => {
    const start = entity("fixture:1", "Tobin Rill");
    const target = entity("fixture:3", "Sera Loom");
    const session = {
      start,
      target,
      moves: 2,
      trail: [
        { qid: start.qid, label: start.label },
        { qid: "fixture:2", label: "Paper Moon Libretto" },
        { qid: target.qid, label: target.label },
      ],
    } satisfies Pick<SessionSnapshot, "start" | "target" | "moves" | "trail">;

    expect(routeRecap(session)).toBe(
      "You connected Tobin Rill to Sera Loom in 2 moves, passing through Paper Moon Libretto.",
    );
  });

  it("handles a direct route with singular move copy", () => {
    const start = entity("fixture:1", "Start");
    const target = entity("fixture:2", "Target");

    expect(
      routeRecap({
        start,
        target,
        moves: 1,
        trail: [
          { qid: start.qid, label: start.label },
          { qid: target.qid, label: target.label },
        ],
      }),
    ).toBe("You connected Start to Target in 1 move.");
  });
});
