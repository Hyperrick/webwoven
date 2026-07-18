import type { RoomSnapshot, SessionSnapshot } from "../api/types";

export type AppRoute =
  | { name: "home"; path: "/" }
  | { name: "solo"; path: "/play/solo" }
  | { name: "daily"; path: "/play/daily" }
  | { name: "lobby"; path: "/lobby" }
  | { name: "lobby-invite"; path: string; code: string }
  | { name: "race"; path: string; code: string }
  | { name: "results"; path: "/results" }
  | { name: "relay-results"; path: string; code: string }
  | { name: "lab"; path: "/lab" }
  | { name: "privacy"; path: "/privacy" }
  | { name: "not-found"; path: string };

export function parseRoute(pathname: string): AppRoute {
  const normalized =
    pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  if (normalized === "/") return { name: "home", path: "/" };
  if (normalized === "/play/solo") return { name: "solo", path: "/play/solo" };
  if (normalized === "/play/daily")
    return { name: "daily", path: "/play/daily" };
  if (normalized === "/lobby" || normalized === "/relay")
    return { name: "lobby", path: "/lobby" };
  if (normalized === "/results") return { name: "results", path: "/results" };
  if (normalized === "/lab") return { name: "lab", path: "/lab" };
  if (normalized === "/privacy") return { name: "privacy", path: "/privacy" };
  const inviteMatch = normalized.match(
    /^\/(?:lobby|relay)\/([0-9A-HJKMNP-TV-Z]{6})\/join$/i,
  );
  if (inviteMatch) {
    const code = inviteMatch[1].toUpperCase();
    return { name: "lobby-invite", path: `/lobby/${code}/join`, code };
  }
  const relayResultsMatch = normalized.match(
    /^\/(?:lobby|relay)\/([0-9A-HJKMNP-TV-Z]{6})\/results$/i,
  );
  if (relayResultsMatch) {
    const code = relayResultsMatch[1].toUpperCase();
    return {
      name: "relay-results",
      path: `/lobby/${code}/results`,
      code,
    };
  }
  const roomMatch = normalized.match(
    /^\/(?:lobby|relay)\/([0-9A-HJKMNP-TV-Z]{6})$/i,
  );
  if (roomMatch) {
    const code = roomMatch[1].toUpperCase();
    return { name: "race", path: `/lobby/${code}`, code };
  }
  return { name: "not-found", path: normalized };
}

export function completionPath(
  session: Pick<SessionSnapshot, "mode">,
  room?: Pick<RoomSnapshot, "code">,
): string {
  return session.mode === "relay" && room
    ? `/lobby/${room.code}/results`
    : "/results";
}

interface BrowserRouterOptions {
  isProtected: () => boolean;
  onRoute: (route: AppRoute) => void;
  onBlockedNavigation: (targetPath: string) => void;
}

export class BrowserRouter {
  #currentPath: string;
  #pendingPath: string | null = null;
  readonly #options: BrowserRouterOptions;

  constructor(options: BrowserRouterOptions) {
    this.#options = options;
    canonicalizeBrowserRoute();
    this.#currentPath = currentBrowserPath();
  }

  start(): () => void {
    const onPopState = () => {
      const route = canonicalizeBrowserRoute();
      const targetPath = currentBrowserPath();
      if (this.#options.isProtected()) {
        this.#pendingPath = targetPath;
        window.history.pushState({}, "", this.#currentPath);
        this.#options.onBlockedNavigation(targetPath);
        return;
      }
      this.#currentPath = targetPath;
      this.#options.onRoute(route);
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }

  navigate(
    path: string,
    options: { replace?: boolean; bypassGuard?: boolean } = {},
  ): void {
    if (
      this.#options.isProtected() &&
      !options.bypassGuard &&
      path !== this.#currentPath
    ) {
      this.#pendingPath = path;
      this.#options.onBlockedNavigation(path);
      return;
    }
    this.#commit(path, options.replace ?? false);
  }

  confirmPending(): void {
    if (!this.#pendingPath) return;
    const path = this.#pendingPath;
    this.#pendingPath = null;
    this.#commit(path, true);
  }

  dismissPending(): void {
    this.#pendingPath = null;
  }

  #commit(path: string, replace: boolean): void {
    if (replace) window.history.replaceState({}, "", path);
    else window.history.pushState({}, "", path);
    const route = canonicalizeBrowserRoute();
    this.#currentPath = currentBrowserPath();
    this.#options.onRoute(route);
    window.scrollTo({ top: 0, behavior: "instant" });
  }
}

function currentBrowserPath(): string {
  return `${window.location.pathname}${window.location.search}`;
}

function canonicalizeBrowserRoute(): AppRoute {
  const route = parseRoute(window.location.pathname);
  if (route.path !== window.location.pathname) {
    window.history.replaceState(
      {},
      "",
      `${route.path}${window.location.search}`,
    );
  }
  return route;
}
