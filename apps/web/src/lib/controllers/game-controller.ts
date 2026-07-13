import type { GameMode, HintType, SessionSnapshot } from "../api/types";
import type { WebwovenApi } from "../api/types";
import { StaleSessionError } from "../api/errors";

function commandId(): string {
  return (
    globalThis.crypto?.randomUUID?.() ??
    `command_${Date.now()}_${Math.random()}`
  );
}

export class GameController {
  readonly #api: WebwovenApi;

  constructor(api: WebwovenApi) {
    this.#api = api;
  }

  start(mode: GameMode, roundId?: string): Promise<SessionSnapshot> {
    return this.#api.createSession({ mode, round_id: roundId });
  }

  resume(sessionId: string): Promise<SessionSnapshot> {
    return this.#api.getSession(sessionId);
  }

  async follow(
    session: SessionSnapshot,
    edgeToken: string,
  ): Promise<SessionSnapshot> {
    const explanation = session.relation_groups
      .flatMap((group) => group.edges)
      .find((edge) => edge.edge_token === edgeToken)?.statement;
    const next = await this.#command(session, {
      type: "follow_edge",
      edge_token: edgeToken,
      client_command_id: commandId(),
      expected_state_version: session.state_version,
    });
    return explanation ? { ...next, last_connection: explanation } : next;
  }

  async back(session: SessionSnapshot): Promise<SessionSnapshot> {
    const next = await this.#command(session, {
      type: "back",
      client_command_id: commandId(),
      expected_state_version: session.state_version,
    });
    return {
      ...next,
      last_connection: `You retraced the route to ${next.current.label}.`,
    };
  }

  hint(
    session: SessionSnapshot,
    hintType: HintType,
    relationPropertyId?: string,
  ): Promise<SessionSnapshot> {
    return this.#command(session, {
      type: "use_hint",
      hint_type: hintType,
      relation_property_id: relationPropertyId,
      client_command_id: commandId(),
      expected_state_version: session.state_version,
    });
  }

  async #command(
    session: SessionSnapshot,
    command: Parameters<WebwovenApi["sendCommand"]>[1],
  ): Promise<SessionSnapshot> {
    try {
      return await this.#api.sendCommand(session.id, command);
    } catch (error) {
      if (error instanceof StaleSessionError) return error.snapshot;
      throw error;
    }
  }
}
