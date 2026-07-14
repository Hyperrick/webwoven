import type { Difficulty, RoomSnapshot } from "../api/types";
import { DEMO_ENTITIES } from "./demo-graph";

function normalizeCode(code: string): string {
  return code
    .trim()
    .toUpperCase()
    .replace(/[^0-9A-HJKMNP-TV-Z]/g, "")
    .slice(0, 6);
}

export class DemoRoomCoordinator {
  #rooms = new Map<string, RoomSnapshot>();

  create(difficulty: Difficulty): RoomSnapshot {
    const room: RoomSnapshot = {
      code: "MAPS27",
      state: "lobby",
      category: "arts_culture",
      difficulty,
      start: DEMO_ENTITIES.Q5586,
      target: DEMO_ENTITIES.Q145,
      max_players: 4,
      players: [
        {
          id: "you",
          display_name: "Guest Cartographer",
          ready: false,
          moves: 0,
          progress: "mapping",
          hints_used: 0,
          is_host: true,
          is_current_guest: true,
        },
        {
          id: "mira",
          display_name: "Mira",
          ready: true,
          moves: 0,
          progress: "mapping",
          hints_used: 0,
        },
      ],
    };
    this.#rooms.set(room.code, room);
    return structuredClone(room);
  }

  join(code: string): RoomSnapshot {
    const normalized = normalizeCode(code);
    const room = this.#rooms.get(normalized);
    if (room) return structuredClone(room);
    const created = this.create("normal");
    const replacement = { ...created, code: normalized || created.code };
    this.#rooms.set(replacement.code, replacement);
    return structuredClone(replacement);
  }

  ready(code: string, ready: boolean): RoomSnapshot {
    return this.#update(code, (room) => ({
      ...room,
      players: room.players.map((player) =>
        player.is_current_guest ? { ...player, ready } : player,
      ),
    }));
  }

  start(code: string, currentSessionId?: string): RoomSnapshot {
    return this.#update(code, (room) => ({
      ...room,
      state: "countdown",
      starts_at: new Date(Date.now() + 5000).toISOString(),
      ...(currentSessionId === undefined
        ? {}
        : { current_session_id: currentSessionId }),
    }));
  }

  get(code: string): RoomSnapshot {
    const room = this.#rooms.get(normalizeCode(code));
    if (!room) throw new Error("That relay room could not be found.");
    return structuredClone(room);
  }

  #update(
    code: string,
    update: (room: RoomSnapshot) => RoomSnapshot,
  ): RoomSnapshot {
    const normalized = normalizeCode(code);
    const current = this.#rooms.get(normalized);
    if (!current) throw new Error("That relay room could not be found.");
    const next = update(current);
    this.#rooms.set(normalized, next);
    return structuredClone(next);
  }
}

export { normalizeCode };
