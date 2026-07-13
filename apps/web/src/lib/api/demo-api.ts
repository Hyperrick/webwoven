import type {
  AppConfig,
  ContentReportInput,
  DailyRound,
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

  async createGuest(displayName = this.#guest.display_name): Promise<Guest> {
    this.#guest = { ...this.#guest, display_name: displayName };
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
    mode: "solo" | "daily";
  }): Promise<SessionSnapshot> {
    const state = createNavigationState(id("session"), input.mode);
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
      next = useHint(current, command.hint_type, command.relation_property_id);
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

  async createRoom(): Promise<RoomSnapshot> {
    return this.#rooms.create();
  }

  async joinRoom(code: string): Promise<RoomSnapshot> {
    return this.#rooms.join(code);
  }

  async setRoomReady(code: string, ready: boolean): Promise<RoomSnapshot> {
    return this.#rooms.ready(code, ready);
  }

  async startRoom(code: string): Promise<RoomSnapshot> {
    return this.#rooms.start(code);
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
