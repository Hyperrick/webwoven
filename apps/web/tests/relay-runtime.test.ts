import { describe, expect, it, vi } from "vitest";
import type {
  EntitySummary,
  RoomSnapshot,
  SessionSnapshot,
} from "../src/lib/api/types";
import type { GameController } from "../src/lib/controllers/game-controller";
import type { RoomController } from "../src/lib/controllers/room-controller";
import { RelayRuntime } from "../src/lib/relay/relay-runtime";

const entity: EntitySummary = {
  qid: "Q1",
  label: "Atlas",
  description: "Test entity",
  category: "people",
  source_kind: "synthetic_fixture",
};

function session(status: SessionSnapshot["status"]): SessionSnapshot {
  return {
    id: "session-1",
    mode: "relay",
    category: "people",
    difficulty: "normal",
    started_at: "2026-07-18T12:00:00Z",
    start: entity,
    target: entity,
    current: entity,
    trail: [{ qid: entity.qid, label: entity.label }],
    moves: 1,
    hints_used: [],
    score: null,
    status,
    state_version: 1,
    shortest_distance: 2,
    elapsed_seconds: 30,
    relation_groups: [],
  };
}

function room(state: RoomSnapshot["state"]): RoomSnapshot {
  return {
    code: "MAPS27",
    state,
    category: "people",
    difficulty: "normal",
    start: entity,
    target: entity,
    max_players: 4,
    current_session_id: "session-1",
    players: [
      {
        id: "guest-1",
        display_name: "Atlas",
        active: true,
        ready: true,
        moves: 1,
        progress: "mapping",
        hints_used: 0,
        is_current_guest: true,
      },
    ],
  };
}

describe("RelayRuntime command reconciliation", () => {
  it("reads the room after an in-flight command before accepting its snapshot", async () => {
    const commandSnapshot = session("active");
    const expiredSnapshot = session("expired");
    let resolveCommand!: (value: SessionSnapshot) => void;
    const command = new Promise<SessionSnapshot>((resolve) => {
      resolveCommand = resolve;
    });
    const follow = vi.fn().mockReturnValue(command);
    const resume = vi.fn().mockResolvedValue(expiredSnapshot);
    let currentRoom = room("grace_period");
    const runtime = new RelayRuntime(
      {} as RoomController,
      { follow, resume } as unknown as GameController,
      {
        route: () => ({
          name: "race",
          path: "/relay/MAPS27",
          code: "MAPS27",
        }),
        session: () => commandSnapshot,
        setRoom: vi.fn(),
        setSession: vi.fn(),
        setConnection: vi.fn(),
        reportStarted: vi.fn(),
        navigate: vi.fn(),
        reportError: vi.fn(),
      },
    );

    const pending = runtime.follow(
      commandSnapshot,
      "edge-token",
      () => currentRoom,
    );
    currentRoom = room("finished");
    resolveCommand(commandSnapshot);

    await expect(pending).resolves.toEqual(expiredSnapshot);
    expect(resume).toHaveBeenCalledOnce();
    expect(resume).toHaveBeenCalledWith("session-1");
  });
});
