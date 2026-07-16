import { describe, expect, it } from "vitest";
import type { SessionSnapshot } from "../src/lib/api/types";
import {
  clearActiveSession,
  loadActiveSessionId,
  persistActiveSession,
} from "../src/lib/navigation/active-session";

class MemoryStorage {
  readonly values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }

  removeItem(key: string): void {
    this.values.delete(key);
  }
}

function session(status: SessionSnapshot["status"]): SessionSnapshot {
  return {
    id: "session-42",
    mode: "solo",
    category: "art_design",
    difficulty: "normal",
    started_at: "2026-07-13T10:00:00Z",
    start: entity("Q1"),
    target: entity("Q2"),
    current: entity("Q1"),
    trail: [{ qid: "Q1", label: "Entity Q1" }],
    moves: 0,
    hints_used: [],
    score: null,
    status,
    state_version: 0,
    shortest_distance: 1,
    elapsed_seconds: 0,
    relation_groups: [],
  };
}

function entity(qid: string): SessionSnapshot["current"] {
  return {
    qid,
    label: `Entity ${qid}`,
    description: "Fixture entity",
    category: "places_architecture",
    source_kind: "synthetic_fixture",
  };
}

describe("active session storage", () => {
  it("persists only the opaque ID for an active mode", () => {
    const storage = new MemoryStorage();
    persistActiveSession(session("active"), storage);

    expect(loadActiveSessionId("solo", storage)).toBe("session-42");
    expect([...storage.values.values()]).toEqual(["session-42"]);
  });

  it("clears completed and explicitly replaced sessions", () => {
    const storage = new MemoryStorage();
    persistActiveSession(session("active"), storage);
    persistActiveSession(session("completed"), storage);
    expect(loadActiveSessionId("solo", storage)).toBeUndefined();

    persistActiveSession(session("active"), storage);
    clearActiveSession("solo", storage);
    expect(loadActiveSessionId("solo", storage)).toBeUndefined();
  });
});
