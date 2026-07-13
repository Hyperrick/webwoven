import type { HintType } from "../api/types";

const HINT_PENALTIES: Record<HintType, number> = {
  compass: 75,
  lens: 150,
  map_fragment: 250,
};

export function hintPenalty(type: HintType): number {
  return HINT_PENALTIES[type];
}

export function calculateScore(input: {
  shortestDistance: number;
  moves: number;
  elapsedSeconds: number;
  timeWindow: number;
  penalties: number;
}): number {
  const safeDistance = Math.max(1, input.shortestDistance);
  const efficiency = safeDistance / Math.max(input.moves, safeDistance);
  const speed = Math.max(0, 1 - input.elapsedSeconds / input.timeWindow);
  const raw =
    Math.round(1000 * (0.8 * efficiency + 0.2 * speed)) - input.penalties;
  return Math.max(0, Math.min(1000, raw));
}
