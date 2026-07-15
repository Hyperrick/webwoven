import type {
  AppConfig,
  ContentReportInput,
  DailyRound,
  Difficulty,
  Guest,
  LeaderboardEntry,
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

function id(prefix: string): string {
  const value =
    globalThis.crypto?.randomUUID?.() ?? Math.random().toString(36).slice(2);
  return `${prefix}_${value}`;
}

export class DemoApi implements WebwovenApi {
  #guest: Guest = { id: "guest_demo", display_name: "Guest Cartographer" };
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
      category: "arts_culture",
      difficulty: "normal",
      optimal_distance: 4,
      completed: false,
    };
  }

  async createSession(input: {
    mode: "solo" | "daily" | "relay";
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
    return structuredClone(next.snapshot);
  }

  async getDailyLeaderboard(): Promise<LeaderboardEntry[]> {
    return [
      {
        rank: 1,
        display_name: "PaperFox",
        score: 987,
        moves: 4,
        elapsed_seconds: 31,
      },
      {
        rank: 2,
        display_name: "Northstar",
        score: 965,
        moves: 4,
        elapsed_seconds: 44,
      },
      {
        rank: 3,
        display_name: "Mira",
        score: 901,
        moves: 5,
        elapsed_seconds: 52,
      },
      {
        rank: 17,
        display_name: this.#guest.display_name,
        score: 824,
        moves: 6,
        elapsed_seconds: 79,
        is_current_guest: true,
      },
    ];
  }

  async createRoom(difficulty: Difficulty): Promise<RoomSnapshot> {
    return this.#rooms.create(difficulty);
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
