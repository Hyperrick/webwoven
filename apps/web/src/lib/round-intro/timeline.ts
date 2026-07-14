export const ROUND_INTRO_DURATION_MS = 5_000;

export type RoundIntroPhase =
  "category" | "endpoints" | "orientation" | "launch" | "complete";

export interface RoundIntroTimeline {
  phase: RoundIntroPhase;
  elapsed_ms: number;
  remaining_ms: number;
  overall: number;
  category: number;
  endpoints: number;
  orientation: number;
  launch: number;
}

function segment(value: number, start: number, end: number): number {
  if (end <= start) return value >= end ? 1 : 0;
  return Math.min(1, Math.max(0, (value - start) / (end - start)));
}

export function roundIntroTimeline(
  startsAt: string | number,
  now = Date.now(),
): RoundIntroTimeline {
  const startTime =
    typeof startsAt === "number" ? startsAt : Date.parse(startsAt);
  const safeStart = Number.isFinite(startTime) ? startTime : now;
  const introStart = safeStart - ROUND_INTRO_DURATION_MS;
  const elapsed = Math.min(
    ROUND_INTRO_DURATION_MS,
    Math.max(0, now - introStart),
  );
  const phase: RoundIntroPhase =
    now >= safeStart
      ? "complete"
      : elapsed < 1_250
        ? "category"
        : elapsed < 3_250
          ? "endpoints"
          : elapsed < 4_550
            ? "orientation"
            : "launch";
  return {
    phase,
    elapsed_ms: elapsed,
    remaining_ms: Math.max(0, safeStart - now),
    overall: elapsed / ROUND_INTRO_DURATION_MS,
    category: segment(elapsed, 0, 1_250),
    endpoints: segment(elapsed, 1_250, 3_250),
    orientation: segment(elapsed, 3_250, 4_550),
    launch: segment(elapsed, 4_550, 5_000),
  };
}
