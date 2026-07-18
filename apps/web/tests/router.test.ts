import { afterEach, describe, expect, it, vi } from "vitest";
import { keepsRelayConnection } from "../src/lib/navigation/route-guards";
import {
  BrowserRouter,
  completionPath,
  parseRoute,
} from "../src/lib/navigation/router";

afterEach(() => vi.unstubAllGlobals());

describe("application routes", () => {
  it.each([
    ["/", "home"],
    ["/play/solo", "solo"],
    ["/play/daily", "daily"],
    ["/lobby", "lobby"],
    ["/lobby/maps27/join", "lobby-invite"],
    ["/lobby/maps27", "race"],
    ["/lobby/maps27/results", "relay-results"],
    ["/relay", "lobby"],
    ["/relay/maps27/join", "lobby-invite"],
    ["/relay/maps27", "race"],
    ["/relay/maps27/results", "relay-results"],
    ["/results", "results"],
    ["/lab", "lab"],
    ["/privacy", "privacy"],
    ["/unknown", "not-found"],
  ])("maps %s to %s", (path, name) => {
    expect(parseRoute(path).name).toBe(name);
  });

  it("normalizes lobby codes", () => {
    expect(parseRoute("/lobby/maps27")).toMatchObject({
      name: "race",
      code: "MAPS27",
      path: "/lobby/MAPS27",
    });
  });

  it("keeps lobby invitations and results distinct from the race URL", () => {
    expect(parseRoute("/lobby/maps27/join")).toMatchObject({
      name: "lobby-invite",
      code: "MAPS27",
    });
    expect(parseRoute("/lobby/maps27/results")).toMatchObject({
      name: "relay-results",
      code: "MAPS27",
    });
  });

  it("keeps multiplayer results attached to their lobby code", () => {
    expect(completionPath({ mode: "relay" }, { code: "MAPS27" })).toBe(
      "/lobby/MAPS27/results",
    );
    expect(completionPath({ mode: "solo" })).toBe("/results");
  });

  it("keeps the lobby stream connected through lobby, race, and results", () => {
    expect(keepsRelayConnection(parseRoute("/lobby"))).toBe(true);
    expect(keepsRelayConnection(parseRoute("/lobby/MAPS27"))).toBe(true);
    expect(keepsRelayConnection(parseRoute("/lobby/MAPS27/results"))).toBe(
      true,
    );
    expect(keepsRelayConnection(parseRoute("/lobby/MAPS27/join"))).toBe(false);
    expect(keepsRelayConnection(parseRoute("/"))).toBe(false);
  });

  it("canonicalizes legacy relay URLs to lobby URLs", () => {
    expect(parseRoute("/relay").path).toBe("/lobby");
    expect(parseRoute("/relay/maps27/join").path).toBe("/lobby/MAPS27/join");
    expect(parseRoute("/relay/maps27/results").path).toBe(
      "/lobby/MAPS27/results",
    );
  });

  it("keeps legacy aliases canonical through history and programmatic navigation", () => {
    let popstate: (() => void) | undefined;
    const location = { pathname: "/", search: "" };
    const updateLocation = (path: string): void => {
      const url = new URL(path, "https://www.webwoven.org");
      location.pathname = url.pathname;
      location.search = url.search;
    };
    const replaceState = vi.fn(
      (_state: unknown, _title: string, path: string) => updateLocation(path),
    );
    const pushState = vi.fn((_state: unknown, _title: string, path: string) =>
      updateLocation(path),
    );
    vi.stubGlobal("window", {
      location,
      history: { pushState, replaceState },
      addEventListener: (type: string, listener: () => void) => {
        if (type === "popstate") popstate = listener;
      },
      removeEventListener: vi.fn(),
      scrollTo: vi.fn(),
    });
    const onRoute = vi.fn();
    const router = new BrowserRouter({
      isProtected: () => false,
      onRoute,
      onBlockedNavigation: vi.fn(),
    });
    router.start();

    updateLocation("/relay/maps27");
    popstate?.();
    expect(location.pathname).toBe("/lobby/MAPS27");
    expect(onRoute).toHaveBeenLastCalledWith(
      expect.objectContaining({ name: "race", path: "/lobby/MAPS27" }),
    );

    router.navigate("/relay/maps27/results");
    expect(location.pathname).toBe("/lobby/MAPS27/results");
    expect(replaceState).toHaveBeenCalled();
  });
});
