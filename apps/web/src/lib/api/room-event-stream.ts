export type RelayConnectionState =
  "connecting" | "connected" | "reconnecting" | "offline";

interface RoomEventEnvelope {
  sequence: number;
  type: string;
  payload: unknown;
}

interface RoomEventCallbacks {
  onEvent: (event: RoomEventEnvelope) => void;
  onStatus: (status: RelayConnectionState) => void;
}

export class RoomEventStream {
  #socket: WebSocket | null = null;
  #retryTimer: number | null = null;
  #pingTimer: number | null = null;
  #stopped = true;
  #attempt = 0;
  #sequence = 0;

  connect(code: string, callbacks: RoomEventCallbacks): () => void {
    this.stop();
    this.#stopped = false;
    this.#open(code, callbacks);
    return () => this.stop();
  }

  stop(): void {
    this.#stopped = true;
    if (this.#retryTimer !== null) window.clearTimeout(this.#retryTimer);
    this.#retryTimer = null;
    this.#clearPing();
    this.#socket?.close(1000, "Route left");
    this.#socket = null;
  }

  #open(code: string, callbacks: RoomEventCallbacks): void {
    callbacks.onStatus(this.#attempt === 0 ? "connecting" : "reconnecting");
    const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${scheme}//${window.location.host}/api/v1/ws/rooms/${code}?after=${this.#sequence}`;
    const socket = new WebSocket(url);
    this.#socket = socket;

    socket.addEventListener("open", () => {
      this.#attempt = 0;
      this.#clearPing();
      this.#pingTimer = window.setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) socket.send("ping");
      }, 25_000);
      callbacks.onStatus("connected");
    });
    socket.addEventListener("message", (message) => {
      if (typeof message.data !== "string" || message.data === "pong") return;
      try {
        const event = JSON.parse(message.data) as RoomEventEnvelope;
        this.#sequence = Math.max(this.#sequence, event.sequence ?? 0);
        if (event.type !== "heartbeat") callbacks.onEvent(event);
      } catch {
        callbacks.onStatus("reconnecting");
      }
    });
    socket.addEventListener("close", () => {
      this.#clearPing();
      if (this.#stopped) return;
      callbacks.onStatus(navigator.onLine ? "reconnecting" : "offline");
      const delay = Math.min(10_000, 750 * 2 ** this.#attempt);
      this.#attempt += 1;
      this.#retryTimer = window.setTimeout(
        () => this.#open(code, callbacks),
        delay,
      );
    });
  }

  #clearPing(): void {
    if (this.#pingTimer !== null) window.clearInterval(this.#pingTimer);
    this.#pingTimer = null;
  }
}
