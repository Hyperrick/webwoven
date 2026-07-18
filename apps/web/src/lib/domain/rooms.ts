import type {
  RoomInvitePreview,
  RoomSnapshot,
  RoundFilters,
} from "../api/types";
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

  create(filters: RoundFilters): RoomSnapshot {
    const room: RoomSnapshot = {
      code: "MAPS27",
      state: "lobby",
      category: filters.category ?? "art_design",
      difficulty: filters.difficulty,
      start: DEMO_ENTITIES.Q5586,
      target: DEMO_ENTITIES.Q145,
      max_players: 4,
      players: [
        {
          id: "you",
          display_name: "Guest Cartographer",
          active: true,
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
          active: true,
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
    const created = this.create({ difficulty: "normal" });
    const replacement = { ...created, code: normalized || created.code };
    this.#rooms.set(replacement.code, replacement);
    return structuredClone(replacement);
  }

  invite(code: string): RoomInvitePreview {
    const room = this.get(code);
    const host =
      room.players.find((player) => player.is_host) ?? room.players[0];
    return {
      code: room.code,
      host_display_name: host?.display_name ?? "A Webwoven explorer",
      state: room.state,
      player_count: room.players.filter((player) => player.active).length,
      max_players: room.max_players,
      is_member: true,
      joinable: room.state === "lobby",
    };
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

  voteRematch(code: string, accept: boolean): RoomSnapshot {
    return this.#update(code, (room) => ({
      ...room,
      players: room.players.map((player) =>
        player.is_current_guest ? { ...player, rematch_vote: accept } : player,
      ),
    }));
  }

  finishSession(sessionId: string): void {
    for (const [code, room] of this.#rooms) {
      if (room.current_session_id !== sessionId) continue;
      const next: RoomSnapshot = {
        ...room,
        state: "finished",
        rematch_ends_at: new Date(Date.now() + 30_000).toISOString(),
        players: room.players.map((player) =>
          player.is_current_guest
            ? {
                ...player,
                progress: "arrived",
                finish_rank: 1,
                rematch_vote: undefined,
              }
            : player,
        ),
      };
      this.#rooms.set(code, next);
      return;
    }
  }

  get(code: string): RoomSnapshot {
    const room = this.#rooms.get(normalizeCode(code));
    if (!room) throw new Error("That lobby could not be found.");
    return structuredClone(room);
  }

  #update(
    code: string,
    update: (room: RoomSnapshot) => RoomSnapshot,
  ): RoomSnapshot {
    const normalized = normalizeCode(code);
    const current = this.#rooms.get(normalized);
    if (!current) throw new Error("That lobby could not be found.");
    const next = update(current);
    this.#rooms.set(normalized, next);
    return structuredClone(next);
  }
}

export { normalizeCode };
