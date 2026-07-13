import { describe, expect, it, vi } from "vitest";
import { HttpApi } from "../src/lib/api/http-api";
import type { WireSession } from "../src/lib/api/wire-types";

const item = {
  qid: "Q1",
  label: "Start",
  description: "Start entity",
  category: "places",
  entity_type: "place",
  image_path: null,
};
const wireSession: WireSession = {
  id: "session",
  mode: "solo",
  status: "active",
  graph_version: "graph",
  round_id: "round",
  category: "places",
  difficulty: "normal",
  start: item,
  target: { ...item, qid: "Q2", label: "Target" },
  current: item,
  navigation_stack: [item],
  trail: [item],
  moves: 0,
  hints_used: [],
  hint_penalty: 0,
  state_version: 0,
  started_at: "2026-07-13T10:00:00Z",
  completed_at: null,
  final_score: null,
  relation_groups: [],
};

describe("HTTP API adapter", () => {
  it("persists the guest CSRF token and maps command response wrappers", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: "guest",
            display_name: "Guest",
            csrf_token: "csrf-123",
          }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(wireSession), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            applied: true,
            duplicate: false,
            hint: null,
            session: { ...wireSession, state_version: 1 },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    const api = new HttpApi({ fetch: fetchMock });

    await api.createGuest();
    const created = await api.createSession({ mode: "solo" });
    const moved = await api.sendCommand(created.id, {
      type: "back",
      client_command_id: "command",
      expected_state_version: 0,
    });

    const sessionRequest = fetchMock.mock.calls[1][1] as RequestInit;
    const commandRequest = fetchMock.mock.calls[2][1] as RequestInit;
    expect(new Headers(sessionRequest.headers).get("X-CSRF-Token")).toBe(
      "csrf-123",
    );
    expect(new Headers(commandRequest.headers).get("X-CSRF-Token")).toBe(
      "csrf-123",
    );
    expect(moved.state_version).toBe(1);
  });
});
