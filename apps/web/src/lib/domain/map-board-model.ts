import type { EntitySummary, RelationGroup } from "../api/types";

export type MapBoardNodeRole =
  "start" | "trail" | "current" | "choice" | "discarded" | "goal";

/** Scene coordinates normalized to the inclusive 0–1 range. */
export interface MapBoardPoint {
  x: number;
  y: number;
  z: number;
}

export interface MapBoardLayout {
  /** Adapters map one layout unit to one rem or another fixed display unit. */
  width_units: number;
  height_units: number;
  minimum_width_units: number;
  minimum_height_units: number;
  column_gap_units: number;
  choice_top_units: number;
  choice_lane_gap_units: number;
  bottom_clearance_units: number;
  choice_lane_count: number;
  current_column: number;
  active_choice_column: number;
}

export interface MapBoardRelation {
  group_id: string;
  property_id: string;
  label: string;
  direction: RelationGroup["direction"];
  glyph: RelationGroup["glyph"];
  hint?: RelationGroup["hint"];
}

export interface MapMoveConnection {
  /** Stable semantic identity; signed command tokens are never persisted. */
  id: string;
  edge_token: string;
  relation: MapBoardRelation;
  statement: string;
}

export interface MapMoveChoice {
  /** Stable across edge-token refreshes and relation-hint changes. */
  id: string;
  source_node_id: string;
  target_node_id: string;
  target: EntitySummary;
  connections: MapMoveConnection[];
  primary_connection_id: string;
  /** Present only for choices in the live, rightmost decision stage. */
  edge_token: string;
  relation: MapBoardRelation;
  statement: string;
}

export interface MapBoardNode {
  /** Stage-scoped visual identity. QIDs remain content identity only. */
  id: string;
  qid: string;
  label: string;
  summary?: EntitySummary;
  roles: MapBoardNodeRole[];
  position: MapBoardPoint;
  choice_ids: string[];
  stage_index: number;
}

export interface MapBoardTrailVisit {
  index: number;
  node_id: string;
  qid: string;
  label: string;
  statement?: string;
  revisited: boolean;
}

export interface MapBoardLink {
  id: string;
  kind: "trail" | "choice" | "discarded";
  source_node_id: string;
  target_node_id: string;
  choice_id?: string;
  statement?: string;
}

export interface MapBoard {
  start_node_id: string;
  current_node_id: string;
  goal_node_id: string;
  nodes: MapBoardNode[];
  links: MapBoardLink[];
  /** Only the rightmost stage is actionable. */
  choices: MapMoveChoice[];
  trail: MapBoardTrailVisit[];
  layout: MapBoardLayout;
}
