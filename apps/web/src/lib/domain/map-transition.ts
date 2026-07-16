import type { SessionSnapshot } from "../api/types";
import type { MapBoard } from "./map-board";

export type MapTransitionKind =
  "initial" | "follow" | "back" | "dead_end_back" | "refresh";

export interface MapTransition {
  kind: MapTransitionKind;
  key: string;
  from_node_id?: string;
  to_node_id: string;
}

export function initialMapTransition(
  board: MapBoard,
  stateVersion: number,
): MapTransition {
  return {
    kind: "initial",
    key: `initial:${stateVersion}`,
    to_node_id: board.current_node_id,
  };
}

/** Describe only the visual movement between two authoritative snapshots. */
export function deriveMapTransition(
  previous: SessionSnapshot,
  next: SessionSnapshot,
  previousBoard: MapBoard,
  nextBoard: MapBoard,
): MapTransition {
  const appendedDecision =
    (next.decision_history?.length ?? 0) >
    (previous.decision_history?.length ?? 0)
      ? next.decision_history?.at(-1)
      : undefined;
  const navigationShrank =
    (next.navigation_stack?.length ?? 0) <
    (previous.navigation_stack?.length ?? 0);
  const backedOutOfDeadEnd =
    appendedDecision?.action === "back" &&
    appendedDecision.choices.length === 0;
  const kind: MapTransitionKind = backedOutOfDeadEnd
    ? "dead_end_back"
    : appendedDecision?.action === "back" || navigationShrank
      ? "back"
      : previous.current.qid !== next.current.qid
        ? "follow"
        : "refresh";
  return {
    kind,
    key: `${kind}:${next.state_version}:${nextBoard.current_node_id}`,
    from_node_id: previousBoard.current_node_id,
    to_node_id: nextBoard.current_node_id,
  };
}
