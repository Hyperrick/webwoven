import type {
  AppConfig,
  Category,
  DailyRound,
  DecisionRelation,
  EntitySummary,
  LeaderboardEntry,
  RelationGroup,
  RoomSnapshot,
  SessionSnapshot,
} from "./types";
import type {
  WireConfig,
  WireDaily,
  WireDecisionRelation,
  WireEntity,
  WireLeaderboard,
  WireRoom,
  WireSession,
} from "./wire-types";
import { sourceMetadataFor } from "../domain/entity-provenance";

function category(value: string): Category {
  if (
    value === "nature_science" ||
    value === "places" ||
    value === "history_people" ||
    value === "arts_culture"
  )
    return value;
  if (value.toLowerCase().includes("science")) return "nature_science";
  if (value.toLowerCase().includes("place")) return "places";
  if (value.toLowerCase().includes("people")) return "history_people";
  return "arts_culture";
}

function entity(value: WireEntity): EntitySummary {
  return {
    qid: value.qid,
    label: value.label,
    description: value.description ?? "A reviewed entity in the Webwoven atlas",
    category: category(value.category),
    ...(value.image_path === null ? {} : { image_path: value.image_path }),
    ...sourceMetadataFor(value.qid),
  };
}

function glyph(propertyId: string): RelationGroup["glyph"] {
  if (["P19", "P69", "P108", "P463"].includes(propertyId)) return "origin";
  if (["P131", "P17", "P36", "P276"].includes(propertyId)) return "place";
  if (["P170", "P50", "P57", "P161", "P175", "P800"].includes(propertyId))
    return "work";
  if (["P361", "P171"].includes(propertyId)) return "part";
  if (["P61", "P138", "P737"].includes(propertyId)) return "influence";
  return "nature";
}

function decisionRelation(value: WireDecisionRelation): DecisionRelation {
  return {
    property_id: value.property_id,
    label: value.label,
    direction: value.direction,
    glyph: glyph(value.property_id),
  };
}

export function mapSession(value: WireSession): SessionSnapshot {
  const started = Date.parse(value.started_at);
  const ended = value.completed_at
    ? Date.parse(value.completed_at)
    : Date.now();
  return {
    id: value.id,
    mode: value.mode,
    category: category(value.category),
    difficulty: value.difficulty,
    started_at: value.started_at,
    start: entity(value.start),
    target: entity(value.target),
    current: entity(value.current),
    trail: value.trail.map((item) => ({ qid: item.qid, label: item.label })),
    navigation_stack: value.navigation_stack.map(entity),
    decision_history: (value.decision_history ?? []).map((stage) => ({
      index: stage.index,
      source: entity(stage.source),
      destination: entity(stage.destination),
      action: stage.action,
      choices: stage.choices.map((choice) => ({
        id: choice.id,
        target: entity(choice.target),
        relation: decisionRelation(choice.relation),
        statement: choice.statement,
        ...(choice.connections === undefined
          ? {}
          : {
              connections: choice.connections.map((connection) => ({
                id: connection.id,
                relation: decisionRelation(connection.relation),
                statement: connection.statement,
              })),
            }),
      })),
      ...(stage.selected_choice_id === null
        ? {}
        : { selected_choice_id: stage.selected_choice_id }),
    })),
    moves: value.moves,
    hints_used: value.hints_used.map((hint) => ({
      type: hint.hint_type,
      penalty: hint.penalty,
      message: hint.message,
    })),
    score: value.final_score,
    status: value.status,
    state_version: value.state_version,
    shortest_distance: value.optimal_distance,
    elapsed_seconds: Number.isFinite(started)
      ? Math.max(0, Math.floor((ended - started) / 1000))
      : 0,
    relation_groups: value.relation_groups.map((group) => ({
      group_id: group.group_id,
      property_id: group.property_id,
      label: group.label,
      direction: group.direction,
      glyph: glyph(group.property_id),
      edges: group.edges.map((edge) => ({
        edge_token: edge.edge_token,
        statement: edge.explanation,
        target: entity(edge.target),
      })),
    })),
  };
}

export function mapDaily(value: WireDaily): DailyRound {
  return {
    round_id: value.round_id,
    date: value.day,
    category: category(value.category),
    difficulty: value.difficulty,
    optimal_distance: value.optimal_distance,
    completed: false,
  };
}

export function mapLeaderboard(value: WireLeaderboard): LeaderboardEntry[] {
  return value.entries.map((entry) => ({
    rank: entry.rank,
    display_name: entry.display_name,
    score: entry.score,
    moves: entry.moves,
    elapsed_seconds: entry.elapsed_seconds,
  }));
}

export function mapRoom(value: WireRoom): RoomSnapshot {
  const current = value.participants.find((participant) => participant.is_self);
  return {
    code: value.code,
    state: value.state,
    category: category(value.category),
    difficulty: value.difficulty,
    start: entity(value.start),
    target: entity(value.target),
    max_players: 4,
    starts_at: value.countdown_ends_at ?? undefined,
    current_session_id: current?.session_id ?? undefined,
    players: value.participants.map((participant) => ({
      id: participant.guest_id,
      display_name: participant.display_name,
      ready: participant.ready,
      moves: participant.moves,
      progress:
        participant.progress_band >= 4
          ? "arrived"
          : participant.progress_band >= 2
            ? "closing-in"
            : "mapping",
      hints_used: participant.hints_used,
      is_host: participant.is_self && value.is_host,
      is_current_guest: participant.is_self,
    })),
  };
}

export function mapConfig(value: WireConfig): AppConfig {
  return {
    graph_build: value.graph_version,
    api_available: true,
    guest_mode: true,
  };
}
