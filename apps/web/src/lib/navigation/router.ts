export type AppRoute =
  | { name: "home"; path: "/" }
  | { name: "solo"; path: "/play/solo" }
  | { name: "daily"; path: "/play/daily" }
  | { name: "lobby"; path: "/relay"; code?: string }
  | { name: "race"; path: string; code: string }
  | { name: "results"; path: "/results" }
  | { name: "lab"; path: "/lab" }
  | { name: "not-found"; path: string };

export function parseRoute(pathname: string): AppRoute {
  const normalized =
    pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  if (normalized === "/") return { name: "home", path: "/" };
  if (normalized === "/play/solo") return { name: "solo", path: "/play/solo" };
  if (normalized === "/play/daily")
    return { name: "daily", path: "/play/daily" };
  if (normalized === "/relay") return { name: "lobby", path: "/relay" };
  if (normalized === "/results") return { name: "results", path: "/results" };
  if (normalized === "/lab") return { name: "lab", path: "/lab" };
  const roomMatch = normalized.match(/^\/relay\/([0-9A-HJKMNP-TV-Z]{6})$/i);
  if (roomMatch) {
    const code = roomMatch[1].toUpperCase();
    return { name: "race", path: `/relay/${code}`, code };
  }
  return { name: "not-found", path: normalized };
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
    this.#currentPath = window.location.pathname;
  }

  start(): () => void {
    const onPopState = () => {
      const targetPath = window.location.pathname;
      if (this.#options.isProtected()) {
        this.#pendingPath = targetPath;
        window.history.pushState({}, "", this.#currentPath);
        this.#options.onBlockedNavigation(targetPath);
        return;
      }
      this.#currentPath = targetPath;
      this.#options.onRoute(parseRoute(targetPath));
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
    this.#currentPath = path;
    this.#options.onRoute(parseRoute(path));
    window.scrollTo({ top: 0, behavior: "instant" });
  }
}
