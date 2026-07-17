import type {
  GameMode,
  HintType,
  RoundFilters,
  SessionSnapshot,
  TrailEntry,
} from "../api/types";
import type { WebwovenApi } from "../api/types";
import { StaleSessionError } from "../api/errors";

function commandId(): string {
  return (
    globalThis.crypto?.randomUUID?.() ??
    `command_${Date.now()}_${Math.random()}`
  );
}

function mergeKnownTrailMetadata(
  known: TrailEntry[],
  authoritative: TrailEntry[],
): TrailEntry[] {
  return authoritative.map((entry, index) => {
    const previous = known[index];
    if (!previous || previous.qid !== entry.qid) return entry;
    return {
      ...entry,
      ...(previous.relation === undefined
        ? {}
        : { relation: previous.relation }),
      ...(previous.revisited === undefined
        ? {}
        : { revisited: previous.revisited }),
    };
  });
}

function annotateAppendedEntry(
  previous: TrailEntry[],
  authoritative: TrailEntry[],
  annotation: Required<Pick<TrailEntry, "qid" | "relation">> &
    Pick<TrailEntry, "revisited">,
): TrailEntry[] | null {
  const appendedIndex = previous.length;
  const prefixMatches = previous.every(
    (entry, index) => authoritative[index]?.qid === entry.qid,
  );
  if (
    !prefixMatches ||
    authoritative.length !== appendedIndex + 1 ||
    authoritative[appendedIndex]?.qid !== annotation.qid
  ) {
    return null;
  }
  return authoritative.map((entry, index) =>
    index === appendedIndex
      ? {
          ...entry,
          relation: annotation.relation,
          ...(annotation.revisited === undefined
            ? {}
            : { revisited: annotation.revisited }),
        }
      : entry,
  );
}

function preserveKnownTrail(
  previous: SessionSnapshot,
  authoritative: SessionSnapshot,
): SessionSnapshot {
  return {
    ...authoritative,
    trail: mergeKnownTrailMetadata(previous.trail, authoritative.trail),
  };
}

interface CommandResult {
  snapshot: SessionSnapshot;
  applied: boolean;
}

export class GameController {
  readonly #api: WebwovenApi;

  constructor(api: WebwovenApi) {
    this.#api = api;
  }

  start(
    mode: GameMode,
    options: Partial<RoundFilters> & { roundId?: string } = {},
  ): Promise<SessionSnapshot> {
    return this.#api.createSession({
      mode,
      ...(options.roundId === undefined ? {} : { round_id: options.roundId }),
      ...(options.difficulty === undefined
        ? {}
        : { difficulty: options.difficulty }),
      ...(options.category === undefined ? {} : { category: options.category }),
    });
  }

  resume(sessionId: string): Promise<SessionSnapshot> {
    return this.#api.getSession(sessionId);
  }

  async follow(
    session: SessionSnapshot,
    edgeToken: string,
  ): Promise<SessionSnapshot> {
    const selectedEdge = session.relation_groups
      .flatMap((group) => group.edges)
      .find((edge) => edge.edge_token === edgeToken);
    const result = await this.#command(session, {
      type: "follow_edge",
      edge_token: edgeToken,
      client_command_id: commandId(),
      expected_state_version: session.state_version,
    });
    const next = result.snapshot;
    if (!result.applied || !selectedEdge) return next;
    const trail = annotateAppendedEntry(session.trail, next.trail, {
      qid: selectedEdge.target.qid,
      relation: selectedEdge.statement,
    });
    return trail
      ? { ...next, trail, last_connection: selectedEdge.statement }
      : next;
  }

  async back(session: SessionSnapshot): Promise<SessionSnapshot> {
    const result = await this.#command(session, {
      type: "back",
      client_command_id: commandId(),
      expected_state_version: session.state_version,
    });
    const next = result.snapshot;
    if (!result.applied) return next;
    const returned = `Returned to ${next.current.label}.`;
    const trail = annotateAppendedEntry(session.trail, next.trail, {
      qid: next.current.qid,
      relation: returned,
      revisited: true,
    });
    if (!trail) return next;
    return {
      ...next,
      trail,
      last_connection: `You retraced the route to ${next.current.label}.`,
    };
  }

  async hint(
    session: SessionSnapshot,
    hintType: HintType,
    relationPropertyId?: string,
    entityQid?: string,
  ): Promise<SessionSnapshot> {
    const result = await this.#command(session, {
      type: "use_hint",
      hint_type: hintType,
      relation_property_id: relationPropertyId,
      entity_qid: entityQid,
      client_command_id: commandId(),
      expected_state_version: session.state_version,
    });
    return result.snapshot;
  }

  async #command(
    session: SessionSnapshot,
    command: Parameters<WebwovenApi["sendCommand"]>[1],
  ): Promise<CommandResult> {
    try {
      const next = await this.#api.sendCommand(session.id, command);
      return { snapshot: preserveKnownTrail(session, next), applied: true };
    } catch (error) {
      if (error instanceof StaleSessionError) {
        return {
          snapshot: preserveKnownTrail(session, error.snapshot),
          applied: false,
        };
      }
      throw error;
    }
  }
}
