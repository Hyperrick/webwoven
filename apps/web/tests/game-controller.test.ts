import { describe, expect, it, vi } from "vitest";
import type {
  EntitySummary,
  RelationGroup,
  SessionSnapshot,
  TrailEntry,
  WebwovenApi,
} from "../src/lib/api/types";
import { StaleSessionError } from "../src/lib/api/errors";
import { GameController } from "../src/lib/controllers/game-controller";

const entities = {
  start: entity("fixture:people:01", "Elian Voss"),
  middle: entity("fixture:people:02", "Gannet Hollow"),
  target: entity("fixture:people:03", "Lantern School"),
  divergent: entity("fixture:people:04", "Nera Sol"),
};

function entity(qid: string, label: string): EntitySummary {
  return {
    qid,
    label,
    description: `${label} description`,
    category: "people",
    source_kind: "synthetic_fixture",
  };
}

function relation(
  token: string,
  target: EntitySummary,
  statement: string,
): RelationGroup[] {
  return [
    {
      group_id: "P131-outgoing-located-in",
      property_id: "P131",
      label: "located in",
      direction: "outgoing",
      glyph: "place",
      edges: [{ edge_token: token, target, statement }],
    },
  ];
}

function snapshot(
  current: EntitySummary,
  trail: TrailEntry[],
  relationGroups: RelationGroup[] = [],
): SessionSnapshot {
  return {
    id: "session-1",
    mode: "solo",
    category: "art_design",
    difficulty: "normal",
    started_at: "2026-07-13T10:00:00Z",
    start: entities.start,
    target: entities.target,
    current,
    trail,
    moves: trail.length - 1,
    hints_used: [],
    score: null,
    status: current.qid === entities.target.qid ? "completed" : "active",
    state_version: trail.length - 1,
    shortest_distance: 2,
    elapsed_seconds: 5,
    relation_groups: relationGroups,
  };
}

function controllerWith(...responses: SessionSnapshot[]) {
  const sendCommand = vi.fn<WebwovenApi["sendCommand"]>();
  for (const response of responses) sendCommand.mockResolvedValueOnce(response);
  const controller = new GameController({
    sendCommand,
  } as unknown as WebwovenApi);
  return { controller, sendCommand };
}

describe("API-backed game controller trail enrichment", () => {
  it("keeps earlier relation metadata across multiple authoritative moves", async () => {
    const firstFact =
      "Fictional fixture fact: Elian Voss was born in Gannet Hollow.";
    const secondFact =
      "Fictional fixture fact: Lantern School is in Gannet Hollow.";
    const initial = snapshot(
      entities.start,
      [{ qid: entities.start.qid, label: entities.start.label }],
      relation("edge-1", entities.middle, firstFact),
    );
    const firstServerResult = snapshot(
      entities.middle,
      [
        { qid: entities.start.qid, label: entities.start.label },
        { qid: entities.middle.qid, label: entities.middle.label },
      ],
      relation("edge-2", entities.target, secondFact),
    );
    const secondServerResult = snapshot(entities.target, [
      { qid: entities.start.qid, label: entities.start.label },
      { qid: entities.middle.qid, label: "Gannet Hollow (canonical)" },
      { qid: entities.target.qid, label: entities.target.label },
    ]);
    const { controller } = controllerWith(
      firstServerResult,
      secondServerResult,
    );

    const first = await controller.follow(initial, "edge-1");
    const second = await controller.follow(first, "edge-2");

    expect(second.trail).toEqual([
      { qid: entities.start.qid, label: entities.start.label },
      {
        qid: entities.middle.qid,
        label: "Gannet Hollow (canonical)",
        relation: firstFact,
      },
      {
        qid: entities.target.qid,
        label: entities.target.label,
        relation: secondFact,
      },
    ]);
    expect(second.last_connection).toBe(secondFact);
  });

  it("marks an appended Back visit while retaining earlier facts", async () => {
    const fact =
      "Fictional fixture fact: Elian Voss was born in Gannet Hollow.";
    const current = snapshot(entities.middle, [
      { qid: entities.start.qid, label: entities.start.label },
      {
        qid: entities.middle.qid,
        label: entities.middle.label,
        relation: fact,
      },
    ]);
    const serverResult = snapshot(entities.start, [
      { qid: entities.start.qid, label: entities.start.label },
      { qid: entities.middle.qid, label: entities.middle.label },
      { qid: entities.start.qid, label: entities.start.label },
    ]);
    const { controller } = controllerWith(serverResult);

    const returned = await controller.back(current);

    expect(returned.trail[1].relation).toBe(fact);
    expect(returned.trail[2]).toEqual({
      qid: entities.start.qid,
      label: entities.start.label,
      relation: "Returned to Elian Voss.",
      revisited: true,
    });
  });

  it("does not merge or append metadata across a server trail divergence", async () => {
    const initial = snapshot(
      entities.middle,
      [
        { qid: entities.start.qid, label: entities.start.label },
        {
          qid: entities.middle.qid,
          label: entities.middle.label,
          relation: "Known relation",
        },
      ],
      relation("edge-3", entities.target, "Chosen relation"),
    );
    const divergentServerResult = snapshot(entities.target, [
      { qid: entities.start.qid, label: entities.start.label },
      { qid: entities.divergent.qid, label: entities.divergent.label },
      { qid: entities.target.qid, label: entities.target.label },
    ]);
    const { controller } = controllerWith(divergentServerResult);

    const result = await controller.follow(initial, "edge-3");

    expect(result.trail).toEqual(divergentServerResult.trail);
    expect(result.last_connection).toBeUndefined();
  });

  it("does not attribute a stale same-target move to the clicked edge", async () => {
    const clickedFact = "The clicked edge used a different relationship.";
    const initial = snapshot(
      entities.start,
      [{ qid: entities.start.qid, label: entities.start.label }],
      relation("edge-stale", entities.middle, clickedFact),
    );
    const concurrentResult = snapshot(entities.middle, [
      { qid: entities.start.qid, label: entities.start.label },
      { qid: entities.middle.qid, label: entities.middle.label },
    ]);
    const sendCommand = vi
      .fn<WebwovenApi["sendCommand"]>()
      .mockRejectedValueOnce(
        new StaleSessionError("Session state is stale", concurrentResult),
      );
    const controller = new GameController({
      sendCommand,
    } as unknown as WebwovenApi);

    const result = await controller.follow(initial, "edge-stale");

    expect(result.trail).toEqual(concurrentResult.trail);
    expect(result.last_connection).toBeUndefined();
  });

  it("sends the exact Compass entity with its relationship", async () => {
    const initial = snapshot(
      entities.start,
      [{ qid: entities.start.qid, label: entities.start.label }],
      relation("edge-compass", entities.middle, "A precise route."),
    );
    const { controller, sendCommand } = controllerWith(initial);

    await controller.hint(initial, "compass", "P131", entities.middle.qid);

    expect(sendCommand).toHaveBeenCalledWith(
      initial.id,
      expect.objectContaining({
        type: "use_hint",
        hint_type: "compass",
        relation_property_id: "P131",
        entity_qid: entities.middle.qid,
      }),
    );
  });
});
