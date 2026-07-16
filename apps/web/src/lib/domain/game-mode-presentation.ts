import type { GameMode } from "../api/types";

const GAME_MODE_LABELS = {
  solo: "Solo route",
  daily: "Daily connection",
  relay: "Live relay",
} as const satisfies Record<GameMode, string>;

export function gameModeLabel(mode: GameMode): string {
  return GAME_MODE_LABELS[mode];
}
