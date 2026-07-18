import type {
  AppConfig,
  Category,
  ContentReportInput,
  DailyLeaderboard,
  DailyRound,
  Difficulty,
  Guest,
  RoomInvitePreview,
  RoundFilters,
  RoomSnapshot,
  SessionCommand,
  SessionSnapshot,
  WebwovenApi,
} from "./types";
import {
  createNavigationState,
  followEdge,
  moveBack,
  type NavigationState,
  useHint,
} from "../domain/navigation";
import { DemoRoomCoordinator } from "../domain/rooms";
import { calculateScore } from "../domain/scoring";

const SAMPLE_DAILY_FIELD = [
  { display_name: "PaperFox", moves: 4, elapsed_seconds: 31 },
  { display_name: "Northstar", moves: 4, elapsed_seconds: 44 },
  { display_name: "Mira", moves: 5, elapsed_seconds: 52 },
].map((entry) => ({
  ...entry,
  rank: 0,
  score: dailyScore(entry.moves, entry.elapsed_seconds),
  is_current_guest: false,
}));

function id(prefix: string): string {
  const value =
    globalThis.crypto?.randomUUID?.() ?? Math.random().toString(36).slice(2);
  return `${prefix}_${value}`;
}

function dailyScore(moves: number, elapsedSeconds: number): number {
  return calculateScore({
    shortestDistance: 4,
    moves,
    elapsedSeconds,
    timeWindow: 180,
    penalties: 0,
  });
}

export class DemoApi implements WebwovenApi {
  #guest: Guest = { id: "guest_demo", display_name: "Explorer GUES" };
  #sessions = new Map<string, NavigationState>();
  #commandResults = new Map<string, SessionSnapshot>();
  #rooms = new DemoRoomCoordinator();
  #roundCursor: Record<Difficulty, number> = { easy: 0, normal: 0, hard: 0 };

  async createGuest(displayName = this.#guest.display_name): Promise<Guest> {
    this.#guest = { ...this.#guest, display_name: displayName };
    return structuredClone(this.#guest);
  }

  async getGuest(): Promise<Guest> {
    return structuredClone(this.#guest);
  }

  async updateGuest(displayName: string): Promise<Guest> {
    return this.createGuest(displayName);
  }

  async getConfig(): Promise<AppConfig> {
    return {
      graph_build: "demo-atlas-2026-07",
      api_available: false,
      guest_mode: true,
    };
  }

  async getDaily(): Promise<DailyRound> {
    return {
      round_id: "daily-demo-wave",
      date: new Date().toISOString().slice(0, 10),
      category: "art_design",
      difficulty: "normal",
      optimal_distance: 4,
      completed: false,
    };
  }

  async createSession(input: {
    mode: "solo" | "daily" | "relay";
    round_id?: string;
    category?: Category;
    difficulty?: Difficulty;
  }): Promise<SessionSnapshot> {
    const difficulty = input.difficulty ?? "normal";
    const routes = {
      easy: [
        { startQid: "Q5586", targetQid: "Q6373", optimalDistance: 2 },
        { startQid: "Q421", targetQid: "Q17", optimalDistance: 2 },
      ],
      normal: [
        { startQid: "Q5586", targetQid: "Q145", optimalDistance: 4 },
        { startQid: "Q149116", targetQid: "Q145", optimalDistance: 3 },
      ],
      hard: [
        { startQid: "Q5586", targetQid: "Q21", optimalDistance: 4 },
        { startQid: "Q5586", targetQid: "Q145", optimalDistance: 4 },
      ],
    }[difficulty];
    const cursor = input.mode === "solo" ? this.#roundCursor[difficulty] : 0;
    if (input.mode === "solo") this.#roundCursor[difficulty] += 1;
    const state = createNavigationState(
      id("session"),
      input.mode,
      difficulty,
      Date.now() + 5000,
      routes[cursor % routes.length],
    );
    this.#sessions.set(state.snapshot.id, state);
    return structuredClone(state.snapshot);
  }

  async getSession(sessionId: string): Promise<SessionSnapshot> {
    return structuredClone(this.#requireSession(sessionId).snapshot);
  }

  async sendCommand(
    sessionId: string,
    command: SessionCommand,
  ): Promise<SessionSnapshot> {
    const duplicate = this.#commandResults.get(command.client_command_id);
    if (duplicate) return structuredClone(duplicate);

    const current = this.#requireSession(sessionId);
    if (Date.now() < Date.parse(current.snapshot.started_at)) {
      throw new Error("This round has not started yet.");
    }
    if (command.expected_state_version !== current.snapshot.state_version) {
      throw new Error(
        "The route changed. The latest position has been restored.",
      );
    }

    let next = current;
    if (command.type === "follow_edge")
      next = followEdge(current, command.edge_token);
    if (command.type === "back") next = moveBack(current);
    if (command.type === "use_hint") {
      next = useHint(
        current,
        command.hint_type,
        command.relation_property_id,
        command.entity_qid,
      );
    }
    this.#sessions.set(sessionId, next);
    this.#commandResults.set(command.client_command_id, next.snapshot);
    if (next.snapshot.mode === "relay" && next.snapshot.status === "completed")
      this.#rooms.finishSession(sessionId);
    return structuredClone(next.snapshot);
  }

  async getDailyLeaderboard(): Promise<DailyLeaderboard> {
    const completed = [...this.#sessions.values()]
      .reverse()
      .find(
        ({ snapshot }) =>
          snapshot.mode === "daily" && snapshot.status === "completed",
      )?.snapshot;
    const ranked = [
      ...SAMPLE_DAILY_FIELD,
      ...(completed
        ? [
            {
              rank: 0,
              display_name: this.#guest.display_name,
              score: completed.score ?? 0,
              moves: completed.moves,
              elapsed_seconds: completed.elapsed_seconds,
              is_current_guest: true,
            },
          ]
        : []),
    ]
      .sort(
        (left, right) =>
          right.score - left.score ||
          left.elapsed_seconds - right.elapsed_seconds ||
          left.moves - right.moves ||
          left.display_name.localeCompare(right.display_name),
      )
      .map((entry, index) => ({ ...entry, rank: index + 1 }));
    const current = ranked.find((entry) => entry.is_current_guest) ?? null;
    return {
      entries: ranked.slice(0, 20),
      current_guest_entry: current,
    };
  }

  async createRoom(filters: RoundFilters): Promise<RoomSnapshot> {
    return this.#rooms.create(filters);
  }

  async getRoomInvite(code: string): Promise<RoomInvitePreview> {
    return this.#rooms.invite(code);
  }

  async joinRoom(code: string): Promise<RoomSnapshot> {
    return this.#rooms.join(code);
  }

  async setRoomReady(code: string, ready: boolean): Promise<RoomSnapshot> {
    return this.#rooms.ready(code, ready);
  }

  async startRoom(code: string): Promise<RoomSnapshot> {
    const sessionId = id("relay");
    const room = this.#rooms.start(code, sessionId);
    const state = createNavigationState(
      sessionId,
      "relay",
      room.difficulty,
      Date.parse(room.starts_at ?? new Date().toISOString()),
    );
    this.#sessions.set(sessionId, state);
    return room;
  }

  async voteRoomRematch(code: string, accept: boolean): Promise<RoomSnapshot> {
    return this.#rooms.voteRematch(code, accept);
  }

  async getRoom(code: string): Promise<RoomSnapshot> {
    return this.#rooms.get(code);
  }

  async reportContent(_input: ContentReportInput): Promise<void> {
    return Promise.resolve();
  }

  #requireSession(sessionId: string): NavigationState {
    const session = this.#sessions.get(sessionId);
    if (!session) throw new Error("That route is no longer available.");
    return session;
  }
}
