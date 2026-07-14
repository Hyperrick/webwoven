import type { MapBoard, MapBoardLink, MapBoardNode } from "./map-board";

export type MapInspectionStatus = "taken" | "not_taken" | "current";

export interface MapInspectionEntity {
  node_id: string;
  qid: string;
  label: string;
}

export interface MapInspectionConnection {
  link_id: string;
  kind: MapBoardLink["kind"];
  source: MapInspectionEntity;
  target: MapInspectionEntity;
  statements: string[];
}

export interface MapNodeInspection extends MapInspectionEntity {
  description: string;
  status: MapInspectionStatus;
  connections: MapInspectionConnection[];
}

const MISSING_DESCRIPTION =
  "No description is available in this graph snapshot.";

/** Historical/current nodes may be inspected without becoming move commands. */
export function isInspectableMapNode(node: MapBoardNode): boolean {
  return ["current", "trail", "discarded"].some((role) => hasRole(node, role));
}

/** Build a fact-preserving inspection view from the immutable map board. */
export function inspectMapNode(
  board: MapBoard,
  nodeId: string,
): MapNodeInspection | undefined {
  const node = board.nodes.find((candidate) => candidate.id === nodeId);
  if (!node || !isInspectableMapNode(node)) return undefined;

  const nodesById = new Map(
    board.nodes.map((candidate) => [candidate.id, candidate]),
  );
  const target = inspectionEntity(node);
  const connections = board.links
    .filter((link) => link.target_node_id === node.id)
    .flatMap((link): MapInspectionConnection[] => {
      const source = nodesById.get(link.source_node_id);
      if (!source) return [];
      return [
        {
          link_id: link.id,
          kind: link.kind,
          source: inspectionEntity(source),
          target,
          statements: statementsFor(link),
        },
      ];
    });

  return {
    ...target,
    description: node.summary?.description.trim() || MISSING_DESCRIPTION,
    status: inspectionStatus(node),
    connections,
  };
}

function inspectionEntity(node: MapBoardNode): MapInspectionEntity {
  return {
    node_id: node.id,
    qid: node.qid,
    label: node.label,
  };
}

function inspectionStatus(node: MapBoardNode): MapInspectionStatus {
  if (hasRole(node, "current")) return "current";
  if (hasRole(node, "discarded")) return "not_taken";
  return "taken";
}

function statementsFor(link: MapBoardLink): string[] {
  const values = [
    ...(link.connections?.map(({ statement }) => statement) ?? []),
    ...(link.statement ? [link.statement] : []),
  ];
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))];
}

function hasRole(node: MapBoardNode, role: string): boolean {
  return (node.roles as readonly string[]).includes(role);
}
