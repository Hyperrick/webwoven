import type {
  AppConfig,
  ContentReportInput,
  DailyRound,
  GameMode,
  Guest,
  LeaderboardEntry,
  RoomSnapshot,
  SessionCommand,
  SessionSnapshot,
  WebwovenApi,
} from "./types";
import { DemoApi } from "./demo-api";
import { HttpApi } from "./http-api";

export class ResilientApi implements WebwovenApi {
  readonly #live: WebwovenApi;
  readonly #demo: WebwovenApi;
  #mode: "undecided" | "live" | "demo" = "undecided";

  constructor(
    live: WebwovenApi = new HttpApi(),
    demo: WebwovenApi = new DemoApi(),
  ) {
    this.#live = live;
    this.#demo = demo;
  }

  get usingDemo(): boolean {
    return this.#mode === "demo";
  }

  createGuest(name?: string): Promise<Guest> {
    return this.#run((api) => api.createGuest(name));
  }

  updateGuest(name: string): Promise<Guest> {
    return this.#run((api) => api.updateGuest(name));
  }

  getConfig(): Promise<AppConfig> {
    return this.#run((api) => api.getConfig());
  }

  getDaily(): Promise<DailyRound> {
    return this.#run((api) => api.getDaily());
  }

  createSession(input: {
    mode: GameMode;
    round_id?: string;
  }): Promise<SessionSnapshot> {
    return this.#run((api) => api.createSession(input));
  }

  getSession(id: string): Promise<SessionSnapshot> {
    return this.#run((api) => api.getSession(id));
  }

  sendCommand(id: string, command: SessionCommand): Promise<SessionSnapshot> {
    return this.#run((api) => api.sendCommand(id, command));
  }

  getDailyLeaderboard(): Promise<LeaderboardEntry[]> {
    return this.#run((api) => api.getDailyLeaderboard());
  }

  createRoom(): Promise<RoomSnapshot> {
    return this.#run((api) => api.createRoom());
  }

  joinRoom(code: string): Promise<RoomSnapshot> {
    return this.#run((api) => api.joinRoom(code));
  }

  setRoomReady(code: string, ready: boolean): Promise<RoomSnapshot> {
    return this.#run((api) => api.setRoomReady(code, ready));
  }

  startRoom(code: string): Promise<RoomSnapshot> {
    return this.#run((api) => api.startRoom(code));
  }

  getRoom(code: string): Promise<RoomSnapshot> {
    return this.#run((api) => api.getRoom(code));
  }

  reportContent(input: ContentReportInput): Promise<void> {
    return this.#run((api) => api.reportContent(input));
  }

  async #run<T>(operation: (api: WebwovenApi) => Promise<T>): Promise<T> {
    if (this.#mode === "demo") return operation(this.#demo);
    if (this.#mode === "live") return operation(this.#live);
    try {
      const result = await operation(this.#live);
      this.#mode = "live";
      return result;
    } catch {
      this.#mode = "demo";
      return operation(this.#demo);
    }
  }
}
