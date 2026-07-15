import type {
  GameMode,
  HintOutcome,
  HintType,
  RoomState,
  SessionStatus,
} from "./types";

export interface WireEntity {
  qid: string;
  label: string;
  description: string | null;
  category: string;
  entity_type: string;
  image_path: string | null;
}

export interface WireDecisionRelation {
  property_id: string;
  label: string;
  direction: "outgoing" | "incoming";
}

export interface WireDecisionConnection {
  id: string;
  relation: WireDecisionRelation;
  statement: string;
}

export interface WireDecisionChoice {
  id: string;
  target: WireEntity;
  relation: WireDecisionRelation;
  statement: string;
  /** Optional only while reading pre-grouping responses and fixtures. */
  connections?: WireDecisionConnection[];
}

export interface WireDecisionStage {
  index: number;
  source: WireEntity;
  destination: WireEntity;
  action: "follow" | "back";
  choices: WireDecisionChoice[];
  selected_choice_id: string | null;
}

export interface WireSession {
  id: string;
  mode: GameMode;
  status: SessionStatus;
  graph_version: string;
  round_id: string;
  category: string;
  difficulty: "easy" | "normal" | "hard";
  optimal_distance: number;
  start: WireEntity;
  target: WireEntity;
  current: WireEntity;
  navigation_stack: WireEntity[];
  trail: WireEntity[];
  /** Optional only while reading pre-history fixtures or cached development responses. */
  decision_history?: WireDecisionStage[];
  moves: number;
  hints_used: Array<{
    hint_type: HintType;
    penalty: number;
    relation_property_id: string | null;
    entity_qid: string | null;
    message: string;
    used_at: string;
    outcome?: HintOutcome | null;
  }>;
  hint_penalty: number;
  state_version: number;
  started_at: string;
  completed_at: string | null;
  final_score: number | null;
  relation_groups: Array<{
    group_id: string;
    property_id: string;
    label: string;
    direction: "outgoing" | "incoming";
    edges: Array<{
      edge_token: string;
      explanation: string;
      target: WireEntity;
    }>;
  }>;
}

export interface WireCommandResponse {
  applied: boolean;
  duplicate: boolean;
  session: WireSession;
}

export interface WireDaily {
  day: string;
  graph_version: string;
  round_id: string;
  category: string;
  difficulty: "easy" | "normal" | "hard";
  optimal_distance: number;
  time_window: number;
  start: WireEntity;
  target: WireEntity;
}

export interface WireLeaderboard {
  day: string;
  entries: Array<{
    rank: number;
    display_name: string;
    score: number;
    moves: number;
    hints_used: number;
    elapsed_seconds: number;
    completed_at: string;
  }>;
}

export interface WireRoom {
  code: string;
  state: RoomState;
  is_host: boolean;
  graph_version: string;
  round_id: string;
  category: string;
  difficulty: "easy" | "normal" | "hard";
  start: WireEntity;
  target: WireEntity;
  participants: Array<{
    guest_id: string;
    display_name: string;
    is_self: boolean;
    ready: boolean;
    connected: boolean;
    session_id: string | null;
    moves: number;
    hints_used: number;
    progress_band: number;
    finish_rank: number | null;
  }>;
  sequence: number;
  countdown_ends_at: string | null;
  grace_ends_at: string | null;
}

export interface WireConfig {
  api_version: "v1";
  graph_version: string;
  categories: string[];
  difficulties: string[];
  modes: string[];
  daily_rollover_timezone: "UTC";
  room_min_players: 2;
  room_max_players: 4;
}
