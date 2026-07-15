import type { Guest } from "../api/types";

const CONFIRMATION_PREFIX = "webwoven.guest-name-confirmed";
const RESERVED_WORDS = new Set(["admin", "moderator", "system", "webwoven"]);
const ALLOWED_NAME = /^[\p{L}\p{N}][\p{L}\p{N} '’\-]*[\p{L}\p{N}]$/u;

type ConfirmationStorage = Pick<Storage, "getItem" | "setItem">;

export function normalizeGuestName(value: string): string {
  return value.normalize("NFKC").trim().split(/\s+/u).join(" ");
}

export function guestNameError(value: string): string | null {
  const name = normalizeGuestName(value);
  const length = Array.from(name).length;
  if (length < 2 || length > 24) return "Use between 2 and 24 characters.";
  if (!ALLOWED_NAME.test(name))
    return "Use letters, numbers, spaces, apostrophes, or hyphens only.";
  const words = name
    .replaceAll(/[-'’]/gu, " ")
    .split(" ")
    .map((word) => word.toLocaleLowerCase());
  if (words.some((word) => RESERVED_WORDS.has(word)))
    return "Choose a name that does not imply an official Webwoven role.";
  return null;
}

export function generatedGuestName(guest: Guest): string {
  return `Explorer ${guest.id.slice(0, 4).toUpperCase()}`;
}

export function isGeneratedGuestName(guest: Guest): boolean {
  return guest.display_name === generatedGuestName(guest);
}

export function isGuestNameConfirmed(
  guest: Guest,
  storage: ConfirmationStorage = localStorage,
): boolean {
  return (
    !isGeneratedGuestName(guest) ||
    storage.getItem(confirmationKey(guest.id)) === "1"
  );
}

export function confirmGuestName(
  guest: Guest,
  storage: ConfirmationStorage = localStorage,
): void {
  storage.setItem(confirmationKey(guest.id), "1");
}

function confirmationKey(guestId: string): string {
  return `${CONFIRMATION_PREFIX}:${guestId}`;
}
