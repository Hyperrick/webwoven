interface RelayRoomTiming {
  state: string;
  grace_ends_at?: unknown;
}

export function relayGraceDeadline(room: RelayRoomTiming): string | null {
  const value = room.grace_ends_at;
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

export function relayGraceRemainingSeconds(
  room: RelayRoomTiming,
  now: number,
): number | null {
  if (room.state !== "grace_period") return null;
  const deadline = relayGraceDeadline(room);
  if (deadline === null) return null;
  const deadlineMs = Date.parse(deadline);
  if (!Number.isFinite(deadlineMs) || !Number.isFinite(now)) return null;
  return Math.max(0, Math.ceil((deadlineMs - now) / 1_000));
}

export function formatRelayGrace(seconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(safeSeconds / 60);
  return `${String(minutes).padStart(2, "0")}:${String(safeSeconds % 60).padStart(2, "0")}`;
}
