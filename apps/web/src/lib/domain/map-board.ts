import type {
  EntitySummary,
  RelationGroup,
  SessionSnapshot,
  TrailEntry,
} from "../api/types";

export type MapBoardNodeRole =
  "start" | "trail" | "current" | "choice" | "goal";

/** Scene coordinates normalized to the inclusive 0–1 range. */
export interface MapBoardPoint {
  x: number;
  y: number;
  z: number;
}

export interface MapBoardLayout {
  /** Adapters may map one layout unit to one rem or another fixed display unit. */
  height_units: number;
  minimum_height_units: number;
  choice_top_units: number;
  choice_lane_gap_units: number;
  bottom_clearance_units: number;
  choice_lane_count: number;
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
  /** Stable semantic identity; the signed command token is deliberately excluded. */
  id: string;
  edge_token: string;
  relation: MapBoardRelation;
  /** Complete fact sentence supplied by the graph; never a relation-label rewrite. */
  statement: string;
}

export interface MapMoveChoice {
  /** Stable across edge-token refreshes and relation-hint changes. */
  id: string;
  source_node_id: string;
  target_node_id: string;
  target: EntitySummary;
  /** Every semantic way the current entity connects to this destination. */
  connections: MapMoveConnection[];
  primary_connection_id: string;
  /** Compatibility projection of the deterministic primary connection. */
  edge_token: string;
  relation: MapBoardRelation;
  statement: string;
}

export interface MapBoardNode {
  id: string;
  qid: string;
  label: string;
  /** Missing only for historical trail entities absent from the current API payload. */
  summary?: EntitySummary;
  roles: MapBoardNodeRole[];
  position: MapBoardPoint;
  choice_ids: string[];
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
  kind: "trail" | "choice";
  source_node_id: string;
  target_node_id: string;
  choice_id?: string;
  /** Exact edge or trail statement when one is available. */
  statement?: string;
}

export interface MapBoard {
  start_node_id: string;
  current_node_id: string;
  goal_node_id: string;
  nodes: MapBoardNode[];
  links: MapBoardLink[];
  choices: MapMoveChoice[];
  trail: MapBoardTrailVisit[];
  layout: MapBoardLayout;
}

interface ChoiceCandidate {
  edge_token: string;
  target: EntitySummary;
  relation: MapBoardRelation;
  statement: string;
  semantic_key: string;
}

const ROLE_ORDER: MapBoardNodeRole[] = [
  "start",
  "trail",
  "current",
  "choice",
  "goal",
];
const MINIMUM_HEIGHT_UNITS = 38;
const CHOICE_TOP_UNITS = 12;
const CHOICE_LANE_GAP_UNITS = 7.5;
const BOTTOM_CLEARANCE_UNITS = 10;

function nodeId(qid: string): string {
  return `node:${qid}`;
}

function compareText(left: string, right: string): number {
  if (left === right) return 0;
  return left < right ? -1 : 1;
}

function stableHash(value: string): string {
  let hash = 0x811c9dc5;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(36);
}

function candidateFor(
  sourceQid: string,
  group: RelationGroup,
  edge: RelationGroup["edges"][number],
): ChoiceCandidate {
  const relation: MapBoardRelation = {
    group_id: group.group_id,
    property_id: group.property_id,
    label: group.label,
    direction: group.direction,
    glyph: group.glyph,
    hint: group.hint,
  };
  const semanticKey = [
    sourceQid,
    edge.target.qid,
    group.property_id,
    group.direction,
    group.group_id,
    group.label,
    edge.statement,
  ].join("\u001f");
  return {
    edge_token: edge.edge_token,
    target: edge.target,
    relation,
    statement: edge.statement,
    semantic_key: semanticKey,
  };
}

function connectionFor(
  candidate: ChoiceCandidate,
  occurrence: number,
): MapMoveConnection {
  const baseId = `connection:${stableHash(candidate.semantic_key)}`;
  return {
    id: occurrence === 1 ? baseId : `${baseId}:${occurrence}`,
    edge_token: candidate.edge_token,
    relation: candidate.relation,
    statement: candidate.statement,
  };
}

function primaryConnection(connections: MapMoveConnection[]) {
  return (
    connections.find(
      (connection) => connection.relation.hint === "promising",
    ) ?? connections[0]
  );
}

/** Flattens relation groups, then groups semantic connections by destination. */
export function flattenMoveChoices(snapshot: SessionSnapshot): MapMoveChoice[] {
  const candidates = snapshot.relation_groups
    .flatMap((group) =>
      group.edges.map((edge) =>
        candidateFor(snapshot.current.qid, group, edge),
      ),
    )
    .sort((left, right) => compareText(left.semantic_key, right.semantic_key));
  const byTarget = new Map<string, ChoiceCandidate[]>();
  for (const candidate of candidates) {
    const targetCandidates = byTarget.get(candidate.target.qid) ?? [];
    targetCandidates.push(candidate);
    byTarget.set(candidate.target.qid, targetCandidates);
  }

  return [...byTarget.entries()].map(([targetQid, targetCandidates]) => {
    const occurrences = new Map<string, number>();
    const connections = targetCandidates.map((candidate) => {
      const connectionKey = stableHash(candidate.semantic_key);
      const occurrence = (occurrences.get(connectionKey) ?? 0) + 1;
      occurrences.set(connectionKey, occurrence);
      return connectionFor(candidate, occurrence);
    });
    const primary = primaryConnection(connections);
    const choiceKey = [snapshot.current.qid, targetQid].join("\u001f");
    return {
      id: `choice:${snapshot.current.qid}:${targetQid}:${stableHash(choiceKey)}`,
      source_node_id: nodeId(snapshot.current.qid),
      target_node_id: nodeId(targetQid),
      target: targetCandidates[0].target,
      connections,
      primary_connection_id: primary.id,
      edge_token: primary.edge_token,
      relation: primary.relation,
      statement: primary.statement,
    };
  });
}

function spread(index: number, count: number, start: number, end: number) {
  if (count <= 1) return (start + end) / 2;
  return start + (index / (count - 1)) * (end - start);
}

function depthFor(qid: string): number {
  const bucket = Number.parseInt(stableHash(qid).slice(-2), 36) % 5;
  return 0.46 + bucket * 0.02;
}

function trailVisits(trail: TrailEntry[]): MapBoardTrailVisit[] {
  return trail.map((entry, index) => ({
    index,
    node_id: nodeId(entry.qid),
    qid: entry.qid,
    label: entry.label,
    statement: entry.relation,
    revisited: entry.revisited ?? false,
  }));
}

function uniqueInOrder(values: string[]): string[] {
  return [...new Set(values)];
}

function layoutFor(choiceLaneCount: number): MapBoardLayout {
  const occupiedChoiceHeight =
    choiceLaneCount === 0
      ? 0
      : CHOICE_TOP_UNITS +
        (choiceLaneCount - 1) * CHOICE_LANE_GAP_UNITS +
        BOTTOM_CLEARANCE_UNITS;
  return {
    height_units: Math.max(MINIMUM_HEIGHT_UNITS, occupiedChoiceHeight),
    minimum_height_units: MINIMUM_HEIGHT_UNITS,
    choice_top_units: CHOICE_TOP_UNITS,
    choice_lane_gap_units: CHOICE_LANE_GAP_UNITS,
    bottom_clearance_units: BOTTOM_CLEARANCE_UNITS,
    choice_lane_count: choiceLaneCount,
  };
}

function roleSetFor(
  qid: string,
  snapshot: SessionSnapshot,
  choices: MapMoveChoice[],
): Set<MapBoardNodeRole> {
  const roles = new Set<MapBoardNodeRole>();
  if (qid === snapshot.start.qid) roles.add("start");
  if (snapshot.trail.some((entry) => entry.qid === qid)) roles.add("trail");
  if (qid === snapshot.current.qid) roles.add("current");
  if (choices.some((choice) => choice.target.qid === qid)) roles.add("choice");
  if (qid === snapshot.target.qid) roles.add("goal");
  return roles;
}

function positionFor(
  qid: string,
  roles: Set<MapBoardNodeRole>,
  historical: string[],
  choiceNodes: string[],
  layout: MapBoardLayout,
): MapBoardPoint {
  if (roles.has("current") && roles.has("goal")) {
    return { x: 0.5, y: 0.5, z: 0.52 };
  }
  if (roles.has("current")) return { x: 0.22, y: 0.5, z: 0.52 };
  if (roles.has("goal")) return { x: 0.86, y: 0.5, z: 0.5 };
  if (roles.has("choice")) {
    const index = choiceNodes.indexOf(qid);
    return {
      x: 0.55,
      y:
        (layout.choice_top_units + index * layout.choice_lane_gap_units) /
        layout.height_units,
      z: depthFor(qid),
    };
  }
  const index = historical.indexOf(qid);
  return {
    x: spread(index, historical.length, 0.06, 0.16),
    y: spread(index, historical.length, 0.42, 0.58),
    z: depthFor(qid),
  };
}

function buildLinks(
  choices: MapMoveChoice[],
  trail: MapBoardTrailVisit[],
): MapBoardLink[] {
  const trailLinks = trail.slice(1).map((visit, index): MapBoardLink => {
    const previous = trail[index];
    return {
      id: `trail-link:${index}:${previous.qid}:${visit.qid}`,
      kind: "trail",
      source_node_id: previous.node_id,
      target_node_id: visit.node_id,
      statement: visit.statement,
    };
  });
  return [
    ...trailLinks,
    ...choices.map((choice): MapBoardLink => ({
      id: `link:${choice.id}`,
      kind: "choice",
      source_node_id: choice.source_node_id,
      target_node_id: choice.target_node_id,
      choice_id: choice.id,
      statement: choice.statement,
    })),
  ];
}

/** Builds a deterministic, renderer-independent board for one session state. */
export function buildMapBoard(snapshot: SessionSnapshot): MapBoard {
  const choices = flattenMoveChoices(snapshot);
  const trail = trailVisits(snapshot.trail);
  const summaries = new Map<string, EntitySummary>();
  for (const summary of [
    snapshot.current,
    snapshot.target,
    snapshot.start,
    ...choices.map((choice) => choice.target),
  ]) {
    if (!summaries.has(summary.qid)) summaries.set(summary.qid, summary);
  }
  const trailLabels = new Map(
    snapshot.trail.map((entry) => [entry.qid, entry.label]),
  );
  const qids = new Set([
    snapshot.start.qid,
    snapshot.current.qid,
    snapshot.target.qid,
    ...snapshot.trail.map((entry) => entry.qid),
    ...choices.map((choice) => choice.target.qid),
  ]);
  const choiceNodes = uniqueInOrder(
    choices
      .map((choice) => choice.target.qid)
      .filter(
        (qid) => qid !== snapshot.current.qid && qid !== snapshot.target.qid,
      ),
  );
  const historical = uniqueInOrder([
    ...snapshot.trail.map((entry) => entry.qid),
    snapshot.start.qid,
  ]).filter(
    (qid) =>
      qid !== snapshot.current.qid &&
      qid !== snapshot.target.qid &&
      !choiceNodes.includes(qid),
  );
  const layout = layoutFor(choiceNodes.length);
  const choiceIdsByQid = new Map<string, string[]>();
  for (const choice of choices) {
    const ids = choiceIdsByQid.get(choice.target.qid) ?? [];
    ids.push(choice.id);
    choiceIdsByQid.set(choice.target.qid, ids);
  }
  const nodes = [...qids]
    .map((qid): MapBoardNode => {
      const roles = roleSetFor(qid, snapshot, choices);
      const summary = summaries.get(qid);
      return {
        id: nodeId(qid),
        qid,
        label: summary?.label ?? trailLabels.get(qid) ?? qid,
        summary,
        roles: ROLE_ORDER.filter((role) => roles.has(role)),
        position: positionFor(qid, roles, historical, choiceNodes, layout),
        choice_ids: choiceIdsByQid.get(qid) ?? [],
      };
    })
    .sort(
      (left, right) =>
        left.position.x - right.position.x ||
        left.position.y - right.position.y ||
        compareText(left.qid, right.qid),
    );

  return {
    start_node_id: nodeId(snapshot.start.qid),
    current_node_id: nodeId(snapshot.current.qid),
    goal_node_id: nodeId(snapshot.target.qid),
    nodes,
    links: buildLinks(choices, trail),
    choices,
    trail,
    layout,
  };
}
