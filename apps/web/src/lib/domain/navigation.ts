import type {
  DecisionChoice,
  DecisionStage,
  Difficulty,
  GameMode,
  HintType,
  RelationGroup,
  SessionSnapshot,
} from "../api/types";
import {
  DEMO_ENTITIES,
  demoDistanceToTarget,
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

export interface DemoRoute {
  startQid: string;
  targetQid: string;
  optimalDistance: number;
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

function decisionChoiceId(group: RelationGroup, targetQid: string): string {
  return [group.property_id, group.direction, targetQid].join(":");
}

function decisionChoices(snapshot: SessionSnapshot): DecisionChoice[] {
  return snapshot.relation_groups.flatMap((group) =>
    group.edges.map((edge) => ({
      id: decisionChoiceId(group, edge.target.qid),
      target: edge.target,
      relation: {
        property_id: group.property_id,
        label: group.label,
        direction: group.direction,
        glyph: group.glyph,
      },
      statement: edge.statement,
    })),
  );
}

function resolvedStage(
  snapshot: SessionSnapshot,
  destination: SessionSnapshot["current"],
  action: DecisionStage["action"],
  selectedEdgeToken?: string,
): DecisionStage {
  const selected = selectedEdgeToken
    ? snapshot.relation_groups
        .flatMap((group) => group.edges.map((edge) => ({ group, edge })))
        .find(({ edge }) => edge.edge_token === selectedEdgeToken)
    : undefined;
  return {
    index: snapshot.decision_history?.length ?? 0,
    source: snapshot.current,
    destination,
    action,
    choices: decisionChoices(snapshot),
    ...(selected
      ? {
          selected_choice_id: decisionChoiceId(
            selected.group,
            selected.edge.target.qid,
          ),
        }
      : {}),
  };
}

export function createNavigationState(
  id: string,
  mode: GameMode,
  difficulty: Difficulty = "normal",
  scheduledStart = Date.now(),
  route: DemoRoute = {
    startQid: "Q5586",
    targetQid: "Q145",
    optimalDistance: 4,
  },
): NavigationState {
  const start = DEMO_ENTITIES[route.startQid];
  const target = DEMO_ENTITIES[route.targetQid];
  return {
    stack: [start.qid],
    startedAt: scheduledStart,
    snapshot: {
      id,
      mode,
      category: start.category,
      difficulty,
      started_at: new Date(scheduledStart).toISOString(),
      start,
      target,
      current: start,
      trail: [{ qid: start.qid, label: start.label, summary: start }],
      navigation_stack: [start],
      decision_history: [],
      moves: 0,
      hints_used: [],
      score: 1000,
      status: "active",
      state_version: 0,
      shortest_distance: route.optimalDistance,
      elapsed_seconds: 0,
      relation_groups: relationGroupsFor(start.qid, new Set([start.qid])),
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
  if (state.stack.includes(resolved.target)) {
    throw new Error(
      "That entity is already in your active route. Use Back to retrace your path.",
    );
  }

  const entity = DEMO_ENTITIES[resolved.target];
  const completed = entity.qid === state.snapshot.target.qid;
  const decision = resolvedStage(state.snapshot, entity, "follow", edgeToken);
  const trail = [
    ...state.snapshot.trail,
    {
      qid: entity.qid,
      label: entity.label,
      summary: entity,
      relation: resolved.statement,
    },
  ];
  const next: NavigationState = {
    ...state,
    stack: [...state.stack, entity.qid],
    snapshot: {
      ...state.snapshot,
      current: entity,
      navigation_stack: [...(state.snapshot.navigation_stack ?? []), entity],
      decision_history: [...(state.snapshot.decision_history ?? []), decision],
      trail,
      moves: state.snapshot.moves + 1,
      status: completed ? "completed" : "active",
      state_version: state.snapshot.state_version + 1,
      relation_groups: relationGroupsFor(
        entity.qid,
        new Set([...state.stack, entity.qid]),
      ),
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
  const decision = resolvedStage(state.snapshot, entity, "back");
  const trail = [
    ...state.snapshot.trail,
    {
      qid: entity.qid,
      label: entity.label,
      summary: entity,
      relation: `Returned to ${entity.label}.`,
      revisited: true,
    },
  ];
  const next: NavigationState = {
    ...state,
    stack,
    snapshot: {
      ...state.snapshot,
      current: entity,
      navigation_stack: stack.map((qid) => DEMO_ENTITIES[qid]),
      decision_history: [...(state.snapshot.decision_history ?? []), decision],
      trail,
      moves: state.snapshot.moves + 1,
      state_version: state.snapshot.state_version + 1,
      relation_groups: relationGroupsFor(entity.qid, new Set(stack)),
      last_connection: `You retraced the route to ${entity.label}.`,
    },
  };
  return withTiming(next, next.snapshot);
}

export function useHint(
  state: NavigationState,
  type: HintType,
  selectedPropertyId?: string,
  selectedEntityQid?: string,
): NavigationState {
  if (state.snapshot.status !== "active") return state;
  const result = applyHintToGroups(state.snapshot.relation_groups, type, {
    selectedPropertyId,
    selectedEntityQid,
    distanceToTarget: (entityQid) =>
      demoDistanceToTarget(
        entityQid,
        state.snapshot.target.qid,
        new Set(state.stack),
      ),
  });
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
