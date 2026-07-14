import type { EntitySummary, SessionSnapshot } from "../api/types";

/** Resolve the next server-authoritative Back destination for an active round. */
export function activeBackDestination(
  session: Pick<SessionSnapshot, "navigation_stack" | "status">,
): EntitySummary | undefined {
  if (session.status !== "active") return undefined;
  return session.navigation_stack?.at(-2);
}
