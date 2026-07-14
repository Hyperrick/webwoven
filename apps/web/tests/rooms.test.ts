import { describe, expect, it } from "vitest";
import { DemoRoomCoordinator, normalizeCode } from "../src/lib/domain/rooms";

describe("relay room coordination", () => {
  it("normalizes codes using the relay alphabet", () => {
    expect(normalizeCode(" map-s27 ")).toBe("MAPS27");
  });

  it("requires the current explorer to ready before the demo room can start", () => {
    const rooms = new DemoRoomCoordinator();
    const room = rooms.create("normal");
    const ready = rooms.ready(room.code, true);
    const started = rooms.start(room.code);

    expect(ready.players.every((player) => player.ready)).toBe(true);
    expect(started.state).toBe("countdown");
    expect(started.starts_at).toBeTruthy();
  });
});
