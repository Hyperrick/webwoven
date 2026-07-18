import { describe, expect, it } from "vitest";
import { keepsRelayConnection } from "../src/lib/navigation/route-guards";
import { completionPath, parseRoute } from "../src/lib/navigation/router";

describe("application routes", () => {
  it.each([
    ["/", "home"],
    ["/play/solo", "solo"],
    ["/play/daily", "daily"],
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

  it("normalizes relay codes", () => {
    expect(parseRoute("/relay/maps27")).toMatchObject({
      name: "race",
      code: "MAPS27",
    });
  });

  it("keeps lobby invitations and relay results distinct from the race URL", () => {
    expect(parseRoute("/relay/maps27/join")).toMatchObject({
      name: "lobby-invite",
      code: "MAPS27",
    });
    expect(parseRoute("/relay/maps27/results")).toMatchObject({
      name: "relay-results",
      code: "MAPS27",
    });
  });

  it("keeps Relay results attached to their lobby code", () => {
    expect(completionPath({ mode: "relay" }, { code: "MAPS27" })).toBe(
      "/relay/MAPS27/results",
    );
    expect(completionPath({ mode: "solo" })).toBe("/results");
  });

  it("keeps the lobby stream connected through lobby, race, and results", () => {
    expect(keepsRelayConnection(parseRoute("/relay"))).toBe(true);
    expect(keepsRelayConnection(parseRoute("/relay/MAPS27"))).toBe(true);
    expect(keepsRelayConnection(parseRoute("/relay/MAPS27/results"))).toBe(
      true,
    );
    expect(keepsRelayConnection(parseRoute("/relay/MAPS27/join"))).toBe(false);
    expect(keepsRelayConnection(parseRoute("/"))).toBe(false);
  });
});
