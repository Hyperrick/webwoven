import type { Guest, SessionSnapshot } from "../api/types";
import { isGuestNameConfirmed } from "../guest-profile/guest-name";
import type { AppRoute } from "./router";

const NAMED_GUEST_ROUTES = new Set<AppRoute["name"]>([
  "daily",
  "lobby",
  "lobby-invite",
  "race",
  "relay-results",
]);
const RELAY_CONNECTED_ROUTES = new Set<AppRoute["name"]>([
  "lobby",
  "race",
  "relay-results",
]);

export function keepsRelayConnection(route: AppRoute): boolean {
  return RELAY_CONNECTED_ROUTES.has(route.name);
}

export function routeRequiresGuestName(
  guest: Guest | undefined,
  route: AppRoute,
): boolean {
  return Boolean(
    guest && NAMED_GUEST_ROUTES.has(route.name) && !isGuestNameConfirmed(guest),
  );
}

export function isProtectedGame(
  session: SessionSnapshot | undefined,
  route: AppRoute,
): boolean {
  return Boolean(
    session?.status === "active" &&
    ["solo", "daily", "race"].includes(route.name),
  );
}
