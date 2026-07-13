import { StaleSessionError } from "./errors";
import {
  readErrorMessage,
  readJsonResponse,
  type ApiResponseContext,
} from "./response-body";
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
import {
  mapConfig,
  mapDaily,
  mapLeaderboard,
  mapRoom,
  mapSession,
} from "./wire-mappers";
import type {
  WireCommandResponse,
  WireConfig,
  WireDaily,
  WireLeaderboard,
  WireRoom,
  WireSession,
} from "./wire-types";

interface HttpApiOptions {
  baseUrl?: string;
  fetch?: typeof fetch;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
}

export class HttpApi implements WebwovenApi {
  readonly #baseUrl: string;
  readonly #fetch: typeof fetch;
  #csrfToken = "";

  constructor(options: HttpApiOptions = {}) {
    this.#baseUrl = options.baseUrl ?? "";
    this.#fetch = options.fetch ?? globalThis.fetch.bind(globalThis);
  }

  async createGuest(displayName?: string): Promise<Guest> {
    const guest = await this.#request<Guest>("/api/v1/guests", {
      method: "POST",
      body: { display_name: displayName },
    });
    this.#csrfToken = guest.csrf_token ?? "";
    return guest;
  }

  async getGuest(): Promise<Guest> {
    const guest = await this.#request<Guest>("/api/v1/guests/me");
    this.#csrfToken = guest.csrf_token ?? "";
    return guest;
  }

  async updateGuest(displayName: string): Promise<Guest> {
    const guest = await this.#request<Guest>("/api/v1/guests/me", {
      method: "PATCH",
      body: { display_name: displayName },
    });
    this.#csrfToken = guest.csrf_token ?? this.#csrfToken;
    return guest;
  }

  async getConfig(): Promise<AppConfig> {
    return mapConfig(await this.#request<WireConfig>("/api/v1/config"));
  }

  async getDaily(): Promise<DailyRound> {
    return mapDaily(await this.#request<WireDaily>("/api/v1/daily"));
  }

  async createSession(input: {
    mode: GameMode;
    round_id?: string;
  }): Promise<SessionSnapshot> {
    const wire = await this.#request<WireSession>("/api/v1/sessions", {
      method: "POST",
      body: input,
    });
    return mapSession(wire);
  }

  async getSession(id: string): Promise<SessionSnapshot> {
    return mapSession(
      await this.#request<WireSession>(`/api/v1/sessions/${id}`),
    );
  }

  async sendCommand(
    id: string,
    command: SessionCommand,
  ): Promise<SessionSnapshot> {
    const path = `/api/v1/sessions/${id}/commands`;
    const context = { method: "POST", path };
    const response = await this.#send(path, {
      method: "POST",
      body: command,
    });
    if (response.status === 409) {
      const stale = await readJsonResponse<{
        message: string;
        current: WireSession;
      }>(response, context);
      throw new StaleSessionError(stale.message, mapSession(stale.current));
    }
    await this.#assertOk(response, context);
    const body = await readJsonResponse<WireCommandResponse>(response, context);
    return mapSession(body.session);
  }

  async getDailyLeaderboard(): Promise<LeaderboardEntry[]> {
    return mapLeaderboard(
      await this.#request<WireLeaderboard>("/api/v1/leaderboards/daily"),
    );
  }

  async createRoom(): Promise<RoomSnapshot> {
    return mapRoom(
      await this.#request<WireRoom>("/api/v1/rooms", {
        method: "POST",
        body: {},
      }),
    );
  }

  async joinRoom(code: string): Promise<RoomSnapshot> {
    return mapRoom(
      await this.#request<WireRoom>(`/api/v1/rooms/${code}/join`, {
        method: "POST",
      }),
    );
  }

  async setRoomReady(code: string, ready: boolean): Promise<RoomSnapshot> {
    const wire = await this.#request<WireRoom>(`/api/v1/rooms/${code}/ready`, {
      method: "POST",
      body: { ready },
    });
    return mapRoom(wire);
  }

  async startRoom(code: string): Promise<RoomSnapshot> {
    return mapRoom(
      await this.#request<WireRoom>(`/api/v1/rooms/${code}/start`, {
        method: "POST",
      }),
    );
  }

  async getRoom(code: string): Promise<RoomSnapshot> {
    return mapRoom(await this.#request<WireRoom>(`/api/v1/rooms/${code}`));
  }

  async reportContent(input: ContentReportInput): Promise<void> {
    const reason =
      input.reason === "incorrect"
        ? "incorrect"
        : input.reason === "image"
          ? "broken_media"
          : "other";
    const path = "/api/v1/content-reports";
    const context = { method: "POST", path };
    const response = await this.#send(path, {
      method: "POST",
      body: {
        entity_qid: input.entity_qid,
        reason,
        details: input.detail ?? "Flagged from the in-game provenance ledger.",
      },
    });
    await this.#assertOk(response, context);
  }

  async #request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const context = { method: options.method ?? "GET", path };
    const response = await this.#send(path, options);
    await this.#assertOk(response, context);
    if (response.status === 204 || response.status === 205)
      return undefined as T;
    return readJsonResponse<T>(response, context);
  }

  #send(path: string, options: RequestOptions): Promise<Response> {
    const method = options.method ?? "GET";
    const headers = new Headers();
    if (options.body !== undefined)
      headers.set("Content-Type", "application/json");
    if (method !== "GET" && this.#csrfToken)
      headers.set("X-CSRF-Token", this.#csrfToken);
    return this.#fetch(`${this.#baseUrl}${path}`, {
      method,
      credentials: "include",
      headers,
      body:
        options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  }

  async #assertOk(
    response: Response,
    context: ApiResponseContext,
  ): Promise<void> {
    if (response.ok) return;
    let message = `Webwoven API request failed (${response.status} ${context.method} ${context.path}).`;
    message = await readErrorMessage(response, message);
    throw new Error(message);
  }
}
