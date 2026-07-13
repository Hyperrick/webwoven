import type { RoomSnapshot } from "../api/types";

function normalizeCode(code: string): string {
  return code
    .trim()
    .toUpperCase()
    .replace(/[^0-9A-HJKMNP-TV-Z]/g, "")
    .slice(0, 6);
}

export class DemoRoomCoordinator {
  #rooms = new Map<string, RoomSnapshot>();

  create(): RoomSnapshot {
    const room: RoomSnapshot = {
      code: "MAPS27",
      state: "lobby",
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
    const created = this.create();
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

  start(code: string): RoomSnapshot {
    return this.#update(code, (room) => ({
      ...room,
      state: "countdown",
      starts_at: new Date(Date.now() + 3000).toISOString(),
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
