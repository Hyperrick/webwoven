import type { RelationGroup, SessionSnapshot } from "../api/types";
import type {
  MapBoardRelation,
  MapMoveChoice,
  MapMoveConnection,
} from "./map-board-model";

interface ChoiceCandidate {
  edge_token: string;
  target: RelationGroup["edges"][number]["target"];
  relation: MapBoardRelation;
  statement: string;
  semantic_key: string;
}

function compareText(left: string, right: string): number {
  if (left === right) return 0;
  return left < right ? -1 : 1;
}

export function stableMapIdentity(value: string): string {
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
  const baseId = `connection:${stableMapIdentity(candidate.semantic_key)}`;
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

/** Group the live relation edges into one direct, semantic choice per target. */
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
      const connectionKey = stableMapIdentity(candidate.semantic_key);
      const occurrence = (occurrences.get(connectionKey) ?? 0) + 1;
      occurrences.set(connectionKey, occurrence);
      return connectionFor(candidate, occurrence);
    });
    const primary = primaryConnection(connections);
    const choiceKey = [snapshot.current.qid, targetQid].join("\u001f");
    return {
      id: `choice:${snapshot.current.qid}:${targetQid}:${stableMapIdentity(choiceKey)}`,
      source_node_id: `node:${snapshot.current.qid}`,
      target_node_id: `node:${targetQid}`,
      target: targetCandidates[0].target,
      connections,
      primary_connection_id: primary.id,
      edge_token: primary.edge_token,
      relation: primary.relation,
      statement: primary.statement,
    };
  });
}
