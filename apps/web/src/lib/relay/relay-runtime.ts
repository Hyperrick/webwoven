import type { RelayConnectionState } from "../api/room-event-stream";
import { RoomEventStream } from "../api/room-event-stream";
import type { HintType, RoomSnapshot, SessionSnapshot } from "../api/types";
import type { GameController } from "../controllers/game-controller";
import type { RoomController } from "../controllers/room-controller";
import { completionPath } from "../navigation/router";
import type { AppRoute } from "../navigation/router";

interface RelayRuntimeCallbacks {
  route: () => AppRoute;
  session: () => SessionSnapshot | undefined;
  setRoom: (room: RoomSnapshot) => void;
  setSession: (session: SessionSnapshot) => void;
  setConnection: (connection: RelayConnectionState) => void;
  reportStarted: (session: SessionSnapshot) => void;
  navigate: (path: string) => void;
  reportError: (message: string) => void;
}

type RoomSource = () => RoomSnapshot | undefined;

export class RelayRuntime {
  readonly #rooms: RoomController;
  readonly #games: GameController;
  readonly #callbacks: RelayRuntimeCallbacks;
  readonly #events = new RoomEventStream();

  constructor(
    rooms: RoomController,
    games: GameController,
    callbacks: RelayRuntimeCallbacks,
  ) {
    this.#rooms = rooms;
    this.#games = games;
    this.#callbacks = callbacks;
  }

  connect(code: string): void {
    if (import.meta.env.VITE_API_MODE === "demo") return;
    this.#events.connect(code, {
      onStatus: this.#callbacks.setConnection,
      onEvent: () => void this.refresh(code),
    });
  }

  stop(): void {
    this.#events.stop();
  }

  async hydrate(code: string, join = true): Promise<void> {
    const room = join
      ? await this.#rooms.join(code)
      : await this.#rooms.get(code);
    this.#callbacks.setRoom(room);
    if (!room.current_session_id)
      throw new Error("This relay has not assigned your route yet.");
    this.#callbacks.setSession(
      await this.#games.resume(room.current_session_id),
    );
    this.connect(room.code);
    await this.apply(room);
  }

  async refresh(code: string): Promise<void> {
    try {
      await this.apply(await this.#rooms.get(code));
    } catch (caught) {
      this.#callbacks.reportError(
        caught instanceof Error
          ? caught.message
          : "The lobby could not refresh.",
      );
    }
  }

  async navigateAfterCompletion(
    session: SessionSnapshot,
    room?: RoomSnapshot,
  ): Promise<void> {
    if (session.mode === "relay" && room) await this.refresh(room.code);
    const path = completionPath(session, room);
    window.setTimeout(() => {
      if (this.#callbacks.route().path !== path) this.#callbacks.navigate(path);
    }, 300);
  }

  async follow(
    session: SessionSnapshot,
    edgeToken: string,
    room: RoomSource,
  ): Promise<SessionSnapshot> {
    const updated = await this.#games.follow(session, edgeToken);
    return this.#settle(updated, room());
  }

  async back(
    session: SessionSnapshot,
    room: RoomSource,
  ): Promise<SessionSnapshot> {
    const updated = await this.#games.back(session);
    return this.#settle(updated, room());
  }

  async hint(
    session: SessionSnapshot,
    type: HintType,
    room: RoomSource,
    propertyId?: string,
    entityQid?: string,
  ): Promise<SessionSnapshot> {
    const updated = await this.#games.hint(
      session,
      type,
      propertyId,
      entityQid,
    );
    return this.#settle(updated, room());
  }

  async #settle(
    session: SessionSnapshot,
    room?: RoomSnapshot,
  ): Promise<SessionSnapshot> {
    return session.mode === "relay" &&
      room &&
      (room.state === "finished" || room.state === "closed")
      ? this.#games.resume(session.id)
      : session;
  }

  async apply(room: RoomSnapshot): Promise<void> {
    this.#callbacks.setRoom(room);
    const route = this.#callbacks.route();
    const current = room.players.find((player) => player.is_current_guest);
    if (
      (room.state === "countdown" || room.state === "racing") &&
      current?.active &&
      room.current_session_id &&
      (route.name === "lobby" || route.name === "relay-results")
    ) {
      const isNewRound =
        this.#callbacks.session()?.id !== room.current_session_id;
      const session = await this.#games.resume(room.current_session_id);
      this.#callbacks.setSession(session);
      if (isNewRound) this.#callbacks.reportStarted(session);
      this.#callbacks.navigate(`/relay/${room.code}`);
      return;
    }
    if (
      route.name === "race" &&
      (room.state === "finished" || room.state === "closed")
    ) {
      if (room.current_session_id)
        this.#callbacks.setSession(
          await this.#games.resume(room.current_session_id),
        );
      this.#callbacks.navigate(`/relay/${room.code}/results`);
    }
  }
}
