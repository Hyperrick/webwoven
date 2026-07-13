import { describe, expect, it } from "vitest";
import { parseRoute } from "../src/lib/navigation/router";

describe("application routes", () => {
  it.each([
    ["/", "home"],
    ["/play/solo", "solo"],
    ["/play/daily", "daily"],
    ["/relay", "lobby"],
    ["/relay/maps27", "race"],
    ["/results", "results"],
    ["/lab", "lab"],
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
});
