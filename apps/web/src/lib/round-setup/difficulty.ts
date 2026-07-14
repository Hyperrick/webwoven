import type { Difficulty } from "../api/types";

export const DIFFICULTIES: ReadonlyArray<{
  value: Difficulty;
  label: string;
  note: string;
}> = [
  { value: "easy", label: "Easy", note: "Shorter routes, clearer landmarks" },
  { value: "normal", label: "Normal", note: "A balanced atlas expedition" },
  { value: "hard", label: "Hard", note: "Longer routes, subtle connections" },
];

type DifficultyScope = "solo" | "relay";
type StorageReader = Pick<Storage, "getItem">;
type StorageWriter = Pick<Storage, "setItem">;

function storageKey(scope: DifficultyScope): string {
  return `webwoven.difficulty.${scope}`;
}

export function loadDifficulty(
  scope: DifficultyScope,
  storage: StorageReader = window.localStorage,
): Difficulty {
  const value = storage.getItem(storageKey(scope));
  return value === "easy" || value === "hard" || value === "normal"
    ? value
    : "normal";
}

export function persistDifficulty(
  scope: DifficultyScope,
  difficulty: Difficulty,
  storage: StorageWriter = window.localStorage,
): void {
  storage.setItem(storageKey(scope), difficulty);
}
