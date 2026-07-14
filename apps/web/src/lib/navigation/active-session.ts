import type { GameMode, SessionSnapshot } from "../api/types";

type ResumableMode = Extract<GameMode, "solo" | "daily">;
type SessionStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;

const KEY_PREFIX = "webwoven.active-session";

function keyFor(mode: ResumableMode): string {
  return `${KEY_PREFIX}.${mode}`;
}

/** Read only an opaque session ID; command tokens remain in live API snapshots. */
export function loadActiveSessionId(
  mode: ResumableMode,
  storage: SessionStorage = window.sessionStorage,
): string | undefined {
  const value = storage.getItem(keyFor(mode))?.trim();
  return value ? value : undefined;
}

export function persistActiveSession(
  session: SessionSnapshot,
  storage: SessionStorage = window.sessionStorage,
): void {
  if (session.mode === "relay") return;
  if (session.status !== "active") {
    storage.removeItem(keyFor(session.mode));
    return;
  }
  storage.setItem(keyFor(session.mode), session.id);
}

export function clearActiveSession(
  mode: ResumableMode,
  storage: SessionStorage = window.sessionStorage,
): void {
  storage.removeItem(keyFor(mode));
}
