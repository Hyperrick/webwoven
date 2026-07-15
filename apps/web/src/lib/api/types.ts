export type GameMode = "solo" | "daily" | "relay";
export type SessionStatus = "active" | "completed" | "abandoned" | "expired";
export type HintType = "compass" | "lens" | "map_fragment";
export type HintOutcome = "promising" | "longer" | "dead_end";
export type HintMarker = HintOutcome | "unlikely";
export type Difficulty = "easy" | "normal" | "hard";
export type Category =
  "history_people" | "nature_science" | "arts_culture" | "places";
export type EntitySourceKind = "wikidata" | "synthetic_fixture" | "unknown";

export interface EntitySummary {
  qid: string;
  label: string;
  description: string;
  category: Category;
  source_kind: EntitySourceKind;
  image_path?: string;
  fact?: string;
  source_url?: string;
}

export interface RelationEdge {
  edge_token: string;
  target: EntitySummary;
  statement: string;
  hint?: HintMarker;
}

export interface RelationGroup {
  group_id: string;
  property_id: string;
  label: string;
  direction: "outgoing" | "incoming";
  glyph: "origin" | "place" | "work" | "part" | "nature" | "influence";
  edges: RelationEdge[];
  /** Legacy group-level hint retained for cached demo snapshots. */
  hint?: HintMarker;
}

export interface TrailEntry {
  qid: string;
  label: string;
  relation?: string;
  revisited?: boolean;
}

export interface DecisionRelation {
  property_id: string;
  label: string;
  direction: RelationGroup["direction"];
  glyph: RelationGroup["glyph"];
}

export interface DecisionConnection {
  /** Stable fact identity; historical connections never retain signed tokens. */
  id: string;
  relation: DecisionRelation;
  statement: string;
}

export interface DecisionChoice {
  /** Stable target choice identity; historical choices never retain signed tokens. */
  id: string;
  target: EntitySummary;
  /** Primary connection used to summarize the choice. */
  relation: DecisionRelation;
  statement: string;
  /** Optional only while reading legacy fixtures or cached responses. */
  connections?: DecisionConnection[];
}

export interface DecisionStage {
  index: number;
  source: EntitySummary;
  destination: EntitySummary;
  action: "follow" | "back";
  choices: DecisionChoice[];
  selected_choice_id?: string;
}

export interface UsedHint {
  type: HintType;
  penalty: number;
  message: string;
  relation_property_id?: string;
  entity_qid?: string;
  outcome?: HintOutcome;
}

export interface SessionSnapshot {
  id: string;
  mode: GameMode;
  category: Category;
  difficulty: Difficulty;
  started_at: string;
  start: EntitySummary;
  target: EntitySummary;
  current: EntitySummary;
  trail: TrailEntry[];
  /** Present for server snapshots; optional for legacy deterministic fixtures. */
  navigation_stack?: EntitySummary[];
  /** Resolved historical frontiers. Only the current relation groups carry tokens. */
  decision_history?: DecisionStage[];
  moves: number;
  hints_used: UsedHint[];
  score: number | null;
  status: SessionStatus;
  state_version: number;
  shortest_distance: number | null;
  elapsed_seconds: number;
  relation_groups: RelationGroup[];
  last_connection?: string;
}

interface CommandBase {
  client_command_id: string;
  expected_state_version: number;
}

export type SessionCommand =
  | (CommandBase & { type: "follow_edge"; edge_token: string })
  | (CommandBase & { type: "back" })
  | (CommandBase & {
      type: "use_hint";
      hint_type: HintType;
      relation_property_id?: string;
      entity_qid?: string;
    });

export interface Guest {
  id: string;
  display_name: string;
  csrf_token?: string;
}

export interface DailyRound {
  round_id: string;
  date: string;
  category: Category;
  difficulty: Difficulty;
  optimal_distance: number;
  completed: boolean;
}

export interface LeaderboardEntry {
  rank: number;
  display_name: string;
  score: number;
  moves: number;
  elapsed_seconds: number;
  is_current_guest: boolean;
}

export interface DailyLeaderboard {
  entries: LeaderboardEntry[];
  current_guest_entry: LeaderboardEntry | null;
}

export type RoomState =
  "lobby" | "countdown" | "racing" | "grace_period" | "finished" | "closed";

export interface RoomPlayer {
  id: string;
  display_name: string;
  ready: boolean;
  moves: number;
  progress: "mapping" | "closing-in" | "arrived";
  hints_used: number;
  is_host?: boolean;
  is_current_guest?: boolean;
}

export interface RoomSnapshot {
  code: string;
  state: RoomState;
  category: Category;
  difficulty: Difficulty;
  start: EntitySummary;
  target: EntitySummary;
  players: RoomPlayer[];
  max_players: number;
  starts_at?: string;
  current_session_id?: string;
}

export interface AppConfig {
  graph_build: string;
  api_available: boolean;
  guest_mode: boolean;
}

export interface ContentReportInput {
  session_id: string;
  entity_qid: string;
  reason: "incorrect" | "unclear" | "image" | "other";
  detail?: string;
}

export interface WebwovenApi {
  createGuest(displayName?: string): Promise<Guest>;
  getGuest(): Promise<Guest>;
  updateGuest(displayName: string): Promise<Guest>;
  getConfig(): Promise<AppConfig>;
  getDaily(): Promise<DailyRound>;
  createSession(input: {
    mode: GameMode;
    round_id?: string;
    category?: Category;
    difficulty?: Difficulty;
  }): Promise<SessionSnapshot>;
  getSession(id: string): Promise<SessionSnapshot>;
  sendCommand(id: string, command: SessionCommand): Promise<SessionSnapshot>;
  getDailyLeaderboard(): Promise<DailyLeaderboard>;
  createRoom(difficulty: Difficulty): Promise<RoomSnapshot>;
  joinRoom(code: string): Promise<RoomSnapshot>;
  setRoomReady(code: string, ready: boolean): Promise<RoomSnapshot>;
  startRoom(code: string): Promise<RoomSnapshot>;
  getRoom(code: string): Promise<RoomSnapshot>;
  reportContent(input: ContentReportInput): Promise<void>;
}
