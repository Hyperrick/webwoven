import type { GameMode, HintType, SessionSnapshot } from "../api/types";
import {
  DEMO_ENTITIES,
  relationGroupsFor,
  resolveDemoEdge,
} from "./demo-graph";
import { applyHintToGroups } from "./hints";
import { calculateScore } from "./scoring";

export interface NavigationState {
  snapshot: SessionSnapshot;
  stack: string[];
  startedAt: number;
}

function elapsedSeconds(state: NavigationState): number {
  return Math.max(0, Math.floor((Date.now() - state.startedAt) / 1000));
}

function scoreFor(state: NavigationState, elapsed: number): number {
  return calculateScore({
    shortestDistance: state.snapshot.shortest_distance ?? 1,
    moves: state.snapshot.moves,
    elapsedSeconds: elapsed,
    timeWindow: 180,
    penalties: state.snapshot.hints_used.reduce(
      (total, hint) => total + hint.penalty,
      0,
    ),
  });
}

function withTiming(
  state: NavigationState,
  snapshot: SessionSnapshot,
): NavigationState {
  const elapsed = elapsedSeconds(state);
  const next = {
    ...state,
    snapshot: { ...snapshot, elapsed_seconds: elapsed },
  };
  return {
    ...next,
    snapshot: { ...next.snapshot, score: scoreFor(next, elapsed) },
  };
}

export function createNavigationState(
  id: string,
  mode: GameMode,
): NavigationState {
  const start = DEMO_ENTITIES.Q5586;
  return {
    stack: [start.qid],
    startedAt: Date.now(),
    snapshot: {
      id,
      mode,
      start,
      target: DEMO_ENTITIES.Q145,
      current: start,
      trail: [{ qid: start.qid, label: start.label }],
      moves: 0,
      hints_used: [],
      score: 1000,
      status: "active",
      state_version: 0,
      shortest_distance: 4,
      elapsed_seconds: 0,
      relation_groups: relationGroupsFor(start.qid),
    },
  };
}

export function followEdge(
  state: NavigationState,
  edgeToken: string,
): NavigationState {
  if (state.snapshot.status !== "active") return state;
  const resolved = resolveDemoEdge(edgeToken);
  if (!resolved || resolved.source !== state.snapshot.current.qid) {
    throw new Error("That connection no longer belongs to the current entity.");
  }

  const entity = DEMO_ENTITIES[resolved.target];
  const completed = entity.qid === state.snapshot.target.qid;
  const next: NavigationState = {
    ...state,
    stack: [...state.stack, entity.qid],
    snapshot: {
      ...state.snapshot,
      current: entity,
      trail: [
        ...state.snapshot.trail,
        { qid: entity.qid, label: entity.label, relation: resolved.statement },
      ],
      moves: state.snapshot.moves + 1,
      status: completed ? "completed" : "active",
      state_version: state.snapshot.state_version + 1,
      relation_groups: relationGroupsFor(entity.qid),
      last_connection: resolved.statement,
    },
  };
  return withTiming(next, next.snapshot);
}

export function moveBack(state: NavigationState): NavigationState {
  if (state.snapshot.status !== "active" || state.stack.length < 2)
    return state;
  const stack = state.stack.slice(0, -1);
  const entity = DEMO_ENTITIES[stack.at(-1) ?? state.snapshot.start.qid];
  const next: NavigationState = {
    ...state,
    stack,
    snapshot: {
      ...state.snapshot,
      current: entity,
      trail: [
        ...state.snapshot.trail,
        {
          qid: entity.qid,
          label: entity.label,
          relation: `Returned to ${entity.label}.`,
          revisited: true,
        },
      ],
      moves: state.snapshot.moves + 1,
      state_version: state.snapshot.state_version + 1,
      relation_groups: relationGroupsFor(entity.qid),
      last_connection: `You retraced the route to ${entity.label}.`,
    },
  };
  return withTiming(next, next.snapshot);
}

export function useHint(
  state: NavigationState,
  type: HintType,
  selectedPropertyId?: string,
): NavigationState {
  if (state.snapshot.status !== "active") return state;
  const result = applyHintToGroups(
    state.snapshot.relation_groups,
    type,
    selectedPropertyId,
  );
  const next: NavigationState = {
    ...state,
    snapshot: {
      ...state.snapshot,
      hints_used: [...state.snapshot.hints_used, result.hint],
      relation_groups: result.groups,
      state_version: state.snapshot.state_version + 1,
    },
  };
  return withTiming(next, next.snapshot);
}
