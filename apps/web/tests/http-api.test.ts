import { describe, expect, it, vi } from "vitest";
import { HttpApi } from "../src/lib/api/http-api";
import type { WireRoom, WireSession } from "../src/lib/api/wire-types";

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
  optimal_distance: 3,
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
  it("resumes a guest and uses its bound CSRF token", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: "guest",
            display_name: "Guest",
            csrf_token: "csrf-resumed",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(wireSession), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        }),
      );
    const api = new HttpApi({ fetch: fetchMock });

    await api.getGuest();
    await api.createSession({ mode: "solo", difficulty: "hard" });

    expect(fetchMock.mock.calls[0][0]).toBe("/api/v1/guests/me");
    const sessionRequest = fetchMock.mock.calls[1][1] as RequestInit;
    expect(new Headers(sessionRequest.headers).get("X-CSRF-Token")).toBe(
      "csrf-resumed",
    );
    expect(JSON.parse(sessionRequest.body as string)).toEqual({
      mode: "solo",
      difficulty: "hard",
    });
  });

  it("sends the host-selected difficulty when creating a relay", async () => {
    const room: WireRoom = {
      code: "MAPS27",
      state: "lobby",
      is_host: true,
      graph_version: "graph",
      round_id: "round",
      category: "places",
      difficulty: "easy",
      start: item,
      target: { ...item, qid: "Q2", label: "Target" },
      participants: [],
      sequence: 1,
      countdown_ends_at: null,
      grace_ends_at: null,
    };
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(room), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const api = new HttpApi({ fetch: fetchMock });

    await api.createRoom("easy");

    const request = fetchMock.mock.calls[0][1] as RequestInit;
    expect(JSON.parse(request.body as string)).toEqual({ difficulty: "easy" });
  });

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

  it("reports an empty success response with request context", async () => {
    const api = new HttpApi({
      fetch: vi
        .fn<typeof fetch>()
        .mockResolvedValue(new Response(null, { status: 201 })),
    });

    await expect(api.createGuest()).rejects.toThrow(
      "empty API response (201 POST /api/v1/guests)",
    );
  });

  it("reports a non-JSON success response with request context", async () => {
    const api = new HttpApi({
      fetch: vi.fn<typeof fetch>().mockResolvedValue(
        new Response("<html>proxy response</html>", {
          status: 200,
          headers: { "Content-Type": "text/html" },
        }),
      ),
    });

    await expect(api.getConfig()).rejects.toThrow(
      "non-JSON API response (200 GET /api/v1/config)",
    );
  });

  it("reports an empty stale-command response without leaking JSON errors", async () => {
    const api = new HttpApi({
      fetch: vi
        .fn<typeof fetch>()
        .mockResolvedValue(new Response(null, { status: 409 })),
    });

    await expect(
      api.sendCommand("session", {
        type: "back",
        client_command_id: "stale-command",
        expected_state_version: 0,
      }),
    ).rejects.toThrow(
      "empty API response (409 POST /api/v1/sessions/session/commands)",
    );
  });

  it("allows report acknowledgements without a response body", async () => {
    const api = new HttpApi({
      fetch: vi
        .fn<typeof fetch>()
        .mockResolvedValue(new Response(null, { status: 201 })),
    });

    await expect(
      api.reportContent({
        session_id: "session",
        entity_qid: "Q1",
        reason: "unclear",
      }),
    ).resolves.toBeUndefined();
  });
});
