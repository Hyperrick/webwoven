import { describe, expect, it } from "vitest";
import {
  mapLeaderboard,
  mapRoom,
  mapSession,
} from "../src/lib/api/wire-mappers";
import type { WireRoom, WireSession } from "../src/lib/api/wire-types";

const entity = (qid: string, label: string) => ({
  qid,
  label,
  description: null,
  category: "Arts & Culture",
  entity_type: "work",
  image_path: null,
});

const session: WireSession = {
  id: "session-1",
  mode: "solo",
  status: "active",
  graph_version: "graph-1",
  round_id: "round-1",
  category: "arts_culture",
  difficulty: "normal",
  start: entity("Q1", "Start"),
  target: entity("Q3", "Target"),
  current: entity("Q1", "Start"),
  navigation_stack: [entity("Q1", "Start")],
  trail: [entity("Q1", "Start")],
  moves: 0,
  hints_used: [],
  hint_penalty: 0,
  state_version: 0,
  started_at: "2026-07-13T10:00:00Z",
  completed_at: null,
  final_score: null,
  relation_groups: [
    {
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
  ],
};

describe("API wire adapters", () => {
  it("maps server sessions into presentation snapshots without calculating server scores", () => {
    const mapped = mapSession(session);
    expect(mapped.score).toBeNull();
    expect(mapped.shortest_distance).toBeNull();
    expect(mapped.relation_groups[0].glyph).toBe("work");
    expect(mapped.relation_groups[0].edges[0].statement).toBe("A made B.");
    expect(mapped.current.source_url).toContain("Q1");
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
        },
      ],
    });
    const room: WireRoom = {
      code: "MAPS27",
      state: "countdown",
      is_host: true,
      graph_version: "graph-1",
      round_id: "round-1",
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

    expect(leaderboard[0].score).toBe(990);
    expect(mapRoom(room)).toMatchObject({
      current_session_id: "relay-session",
      players: [{ progress: "closing-in", is_host: true }],
    });
  });
});
