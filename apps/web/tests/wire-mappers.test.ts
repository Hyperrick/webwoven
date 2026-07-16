import { describe, expect, it } from "vitest";
import {
  mapLeaderboard,
  mapRoom,
  mapSession,
} from "../src/lib/api/wire-mappers";
import type {
  WireEntity,
  WireRoom,
  WireSession,
} from "../src/lib/api/wire-types";

const entity = (qid: string, label: string): WireEntity => ({
  qid,
  label,
  description: null,
  category: "Arts & Culture",
  entity_type: "work",
  image_path: null,
  image_attribution: null,
});

const session: WireSession = {
  id: "session-1",
  mode: "solo",
  status: "active",
  graph_version: "graph-1",
  round_id: "round-1",
  category: "art_design",
  difficulty: "normal",
  optimal_distance: 3,
  start: entity("Q1", "Start"),
  target: entity("Q3", "Target"),
  current: entity("Q1", "Start"),
  navigation_stack: [entity("Q1", "Start")],
  trail: [entity("Q1", "Start")],
  decision_history: [
    {
      index: 0,
      source: entity("Q1", "Start"),
      destination: entity("Q2", "Middle"),
      action: "follow",
      choices: [
        {
          id: "decision:0:Q1:Q2",
          target: entity("Q2", "Middle"),
          relation: {
            property_id: "P170",
            label: "created by",
            direction: "outgoing",
          },
          statement: "A made B.",
        },
      ],
      selected_choice_id: "decision:0:Q1:Q2",
    },
  ],
  moves: 0,
  hints_used: [],
  hint_penalty: 0,
  state_version: 0,
  started_at: "2026-07-13T10:00:00Z",
  completed_at: null,
  final_score: null,
  relation_groups: [
    {
      group_id: "P170-outgoing-created-by",
      property_id: "P170",
      label: "created by",
      direction: "outgoing",
      edges: [
        {
          edge_token: "signed-edge",
          explanation: "A made B.",
          target: entity("Q2", "Middle"),
        },
      ],
    },
    {
      group_id: "P170-incoming-creator-of",
      property_id: "P170",
      label: "creator of",
      direction: "incoming",
      edges: [
        {
          edge_token: "signed-inverse-edge",
          explanation: "B was made by A.",
          target: entity("Q4", "Inverse middle"),
        },
      ],
    },
  ],
};

describe("API wire adapters", () => {
  it("maps server sessions into presentation snapshots without calculating server scores", () => {
    const mapped = mapSession(session);
    expect(mapped.score).toBeNull();
    expect(mapped.difficulty).toBe("normal");
    expect(mapped.category).toBe("art_design");
    expect(mapped.started_at).toBe("2026-07-13T10:00:00Z");
    expect(mapped.shortest_distance).toBe(3);
    expect(mapped.navigation_stack?.map(({ qid }) => qid)).toEqual(["Q1"]);
    expect(mapped.decision_history).toEqual([
      expect.objectContaining({
        index: 0,
        action: "follow",
        selected_choice_id: "decision:0:Q1:Q2",
        choices: [
          expect.objectContaining({
            id: "decision:0:Q1:Q2",
            statement: "A made B.",
            relation: expect.objectContaining({
              property_id: "P170",
              glyph: "work",
            }),
          }),
        ],
      }),
    ]);
    expect(mapped.decision_history?.[0]?.choices[0]).not.toHaveProperty(
      "connections",
    );
    expect(mapped.relation_groups[0].glyph).toBe("work");
    expect(mapped.relation_groups[0].edges[0].statement).toBe("A made B.");
    expect(mapped.relation_groups.map((group) => group.property_id)).toEqual([
      "P170",
      "P170",
    ]);
    expect(mapped.relation_groups.map((group) => group.group_id)).toEqual([
      "P170-outgoing-created-by",
      "P170-incoming-creator-of",
    ]);
    expect(mapped.relation_groups[1]).toMatchObject({
      direction: "incoming",
      label: "creator of",
    });
    expect(mapped.current).toMatchObject({
      source_kind: "wikidata",
      source_url: "https://www.wikidata.org/wiki/Q1",
    });
  });

  it("preserves complete Commons attribution on entity summaries", () => {
    const attributed = entity("Q1", "Start");
    attributed.image_path = "/media/start.jpg";
    attributed.image_attribution = {
      file_name: "Start.jpg",
      original_url: "https://upload.wikimedia.org/original.jpg",
      derivative_url: "https://upload.wikimedia.org/thumbnail.jpg",
      source_url: "https://commons.wikimedia.org/wiki/File:Start.jpg",
      license_id: "CC_BY_4_0",
      creator: "Example photographer",
      license_url: "https://creativecommons.org/licenses/by/4.0/",
      attribution_text: "Example photographer — CC BY 4.0 — Wikimedia Commons",
      context_label: "Related subject",
    };

    const mapped = mapSession({
      ...session,
      current: attributed,
      navigation_stack: [attributed],
    });

    expect(mapped.current.image_path).toBe("/media/start.jpg");
    expect(mapped.current.image_attribution).toEqual(
      expect.objectContaining({
        creator: "Example photographer",
        license_id: "CC_BY_4_0",
        source_url: "https://commons.wikimedia.org/wiki/File:Start.jpg",
        context_label: "Related subject",
      }),
    );
  });

  it("maps every token-free connection on a grouped historical choice", () => {
    const stage = session.decision_history?.[0];
    if (stage === undefined) throw new Error("history fixture is missing");
    const primary = stage.choices[0];
    if (primary === undefined) throw new Error("choice fixture is missing");
    const mapped = mapSession({
      ...session,
      decision_history: [
        {
          ...stage,
          choices: [
            {
              ...primary,
              connections: [
                {
                  id: "edge-created",
                  relation: {
                    property_id: "P170",
                    label: "created by",
                    direction: "outgoing",
                  },
                  statement: "A made B.",
                },
                {
                  id: "edge-influenced",
                  relation: {
                    property_id: "P737",
                    label: "influenced by",
                    direction: "incoming",
                  },
                  statement: "B influenced A.",
                },
              ],
            },
          ],
        },
      ],
    });
    const connections = mapped.decision_history?.[0]?.choices[0]?.connections;

    expect(connections).toEqual([
      {
        id: "edge-created",
        relation: {
          property_id: "P170",
          label: "created by",
          direction: "outgoing",
          glyph: "work",
        },
        statement: "A made B.",
      },
      {
        id: "edge-influenced",
        relation: {
          property_id: "P737",
          label: "influenced by",
          direction: "incoming",
          glyph: "influence",
        },
        statement: "B influenced A.",
      },
    ]);
    expect(connections?.every((item) => !("edge_token" in item))).toBe(true);
  });

  it("maps an exact hint outcome onto only its selected edge", () => {
    const mapped = mapSession({
      ...session,
      hints_used: [
        {
          hint_type: "lens",
          penalty: 150,
          relation_property_id: "P170",
          entity_qid: "Q2",
          message: "Lens: Middle is on a near-optimal route.",
          used_at: "2026-07-13T10:00:01Z",
          outcome: "promising",
        },
      ],
    });

    expect(mapped.hints_used[0]).toMatchObject({
      entity_qid: "Q2",
      outcome: "promising",
    });
    expect(mapped.relation_groups[0].edges[0].hint).toBe("promising");
    expect(mapped.relation_groups[1].edges[0].hint).toBeUndefined();
  });

  it("does not fabricate Wikidata sources for synthetic fixture entities", () => {
    const fixture = entity("fixture:art_design:01", "Tobin Rill");
    const mapped = mapSession({
      ...session,
      start: fixture,
      current: fixture,
      navigation_stack: [fixture],
      trail: [fixture],
    });

    expect(mapped.current.source_kind).toBe("synthetic_fixture");
    expect(mapped.current.source_url).toBeUndefined();
  });

  it("unwraps leaderboards and maps room participants", () => {
    const leaderboard = mapLeaderboard({
      day: "2026-07-13",
      entries: [
        {
          rank: 1,
          display_name: "Mira",
          score: 990,
          moves: 4,
          hints_used: 0,
          elapsed_seconds: 32,
          completed_at: "2026-07-13T10:01:00Z",
          is_current_guest: true,
        },
      ],
      current_guest_entry: {
        rank: 1,
        display_name: "Mira",
        score: 990,
        moves: 4,
        hints_used: 0,
        elapsed_seconds: 32,
        completed_at: "2026-07-13T10:01:00Z",
        is_current_guest: true,
      },
    });
    const room: WireRoom = {
      code: "MAPS27",
      state: "countdown",
      is_host: true,
      graph_version: "graph-1",
      round_id: "round-1",
      category: "art_design",
      difficulty: "hard",
      start: entity("Q1", "Start"),
      target: entity("Q3", "Target"),
      participants: [
        {
          guest_id: "guest",
          display_name: "You",
          is_self: true,
          ready: true,
          connected: true,
          session_id: "relay-session",
          moves: 2,
          hints_used: 0,
          progress_band: 3,
          finish_rank: null,
        },
      ],
      sequence: 2,
      countdown_ends_at: "2026-07-13T10:00:03Z",
      grace_ends_at: null,
    };

    expect(leaderboard.entries[0].score).toBe(990);
    expect(leaderboard.current_guest_entry?.is_current_guest).toBe(true);
    expect(mapRoom(room)).toMatchObject({
      category: "art_design",
      difficulty: "hard",
      start: { qid: "Q1" },
      target: { qid: "Q3" },
      current_session_id: "relay-session",
      players: [{ progress: "closing-in", is_host: true }],
    });
  });
});
