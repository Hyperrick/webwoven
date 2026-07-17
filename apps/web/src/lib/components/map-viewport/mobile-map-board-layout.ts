import type { MapBoard, MapBoardNode } from "../../domain/map-board";

export const MOBILE_MAP_LAYOUT_MEDIA_QUERY = "(width <= 32rem)";

const WORLD_WIDTH_UNITS = 26;
const MINIMUM_HEIGHT_UNITS = 42;
const TOP_GUTTER_UNITS = 8;
const WORLD_CENTER_UNITS = WORLD_WIDTH_UNITS / 2;
const LEFT_CHOICE_UNITS = 7;
const RIGHT_CHOICE_UNITS = WORLD_WIDTH_UNITS - LEFT_CHOICE_UNITS;
const CHOICE_ROW_GAP_UNITS = 5.5;
const STAGE_GAP_UNITS = 6;
const GOAL_STAGE_GAP_UNITS = 7;
const BOTTOM_CLEARANCE_UNITS = 10;
const ROUTE_NODE_CLEARANCE_UNITS = 6;

interface MobileAnchor {
  x: number;
  y: number;
}

/** Project the deterministic board into a phone-readable top-to-bottom flow. */
export function projectMobileMapBoard(board: MapBoard): MapBoard {
  const stages = groupNodesByStage(board.nodes);
  const anchors = new Map<string, MobileAnchor>();
  let cursorY = TOP_GUTTER_UNITS;
  let lastAnchorY = cursorY;

  stages.forEach((nodes, stageIndex) => {
    if (stageIndex > 0) {
      cursorY += isDistantGoalStage(nodes, board)
        ? GOAL_STAGE_GAP_UNITS
        : STAGE_GAP_UNITS;
    }
    const orderedNodes = [...nodes].sort(compareStageNodes);
    const routeNodes = orderedNodes.filter(isRouteNode);
    const distantGoalNodes = orderedNodes.filter(isDistantGoalNode);
    const constellationNodes = orderedNodes.filter(
      (node) => !isRouteNode(node) && !isDistantGoalNode(node),
    );

    if (constellationNodes.length > 0) {
      const rows = chunkRows(constellationNodes);
      rows.forEach((row, rowIndex) => {
        const rowY = cursorY + rowIndex * CHOICE_ROW_GAP_UNITS;
        row.forEach((node, columnIndex) => {
          anchors.set(node.id, {
            x: constellationX(node, row.length, columnIndex, routeNodes.length),
            y: rowY,
          });
        });
        lastAnchorY = rowY;
      });
      cursorY = lastAnchorY;
    }

    if (routeNodes.length > 0) {
      if (constellationNodes.length > 0) cursorY += ROUTE_NODE_CLEARANCE_UNITS;
      routeNodes.forEach((node, index) => {
        if (index > 0) cursorY += ROUTE_NODE_CLEARANCE_UNITS;
        anchors.set(node.id, { x: WORLD_CENTER_UNITS, y: cursorY });
        lastAnchorY = cursorY;
      });
    }

    if (distantGoalNodes.length > 0) {
      if (constellationNodes.length > 0 || routeNodes.length > 0)
        cursorY += GOAL_STAGE_GAP_UNITS;
      distantGoalNodes.forEach((node, index) => {
        if (index > 0) cursorY += ROUTE_NODE_CLEARANCE_UNITS;
        anchors.set(node.id, { x: WORLD_CENTER_UNITS, y: cursorY });
        lastAnchorY = cursorY;
      });
    }

    cursorY = lastAnchorY;
  });

  const heightUnits = Math.max(
    MINIMUM_HEIGHT_UNITS,
    lastAnchorY + BOTTOM_CLEARANCE_UNITS,
  );

  return {
    ...board,
    nodes: board.nodes.map((node) => {
      const anchor = anchors.get(node.id);
      if (!anchor) return node;
      return {
        ...node,
        position: {
          x: anchor.x / WORLD_WIDTH_UNITS,
          y: anchor.y / heightUnits,
          z: node.position.z,
        },
      };
    }),
    layout: {
      ...board.layout,
      width_units: WORLD_WIDTH_UNITS,
      height_units: heightUnits,
      minimum_width_units: WORLD_WIDTH_UNITS,
      minimum_height_units: MINIMUM_HEIGHT_UNITS,
      choice_top_units: TOP_GUTTER_UNITS,
      choice_lane_gap_units: CHOICE_ROW_GAP_UNITS,
      bottom_clearance_units: BOTTOM_CLEARANCE_UNITS,
    },
  };
}

function groupNodesByStage(nodes: MapBoardNode[]): MapBoardNode[][] {
  const stages = new Map<number, MapBoardNode[]>();
  for (const node of nodes) {
    const stage = stages.get(node.stage_index) ?? [];
    stage.push(node);
    stages.set(node.stage_index, stage);
  }
  return [...stages.entries()]
    .sort(([left], [right]) => left - right)
    .map(([, stage]) => stage);
}

function compareStageNodes(left: MapBoardNode, right: MapBoardNode): number {
  const routeOrder =
    Number(left.roles.includes("trail")) -
    Number(right.roles.includes("trail"));
  return (
    routeOrder ||
    left.position.y - right.position.y ||
    left.id.localeCompare(right.id, "en")
  );
}

function chunkRows(nodes: MapBoardNode[]): MapBoardNode[][] {
  const rows: MapBoardNode[][] = [];
  for (let index = 0; index < nodes.length; index += 2)
    rows.push(nodes.slice(index, index + 2));
  return rows;
}

function constellationX(
  node: MapBoardNode,
  rowLength: number,
  columnIndex: number,
  routeNodeCount: number,
): number {
  if (rowLength === 2)
    return columnIndex === 0 ? LEFT_CHOICE_UNITS : RIGHT_CHOICE_UNITS;
  if (routeNodeCount === 0) return WORLD_CENTER_UNITS;
  return node.position.y <= 0.5 ? LEFT_CHOICE_UNITS : RIGHT_CHOICE_UNITS;
}

function isRouteNode(node: MapBoardNode): boolean {
  return node.roles.includes("trail") || node.roles.includes("current");
}

function isDistantGoalNode(node: MapBoardNode): boolean {
  return (
    node.roles.includes("goal") &&
    !node.roles.includes("choice") &&
    !node.roles.includes("discarded") &&
    !node.roles.includes("trail") &&
    !node.roles.includes("current")
  );
}

function isDistantGoalStage(nodes: MapBoardNode[], board: MapBoard): boolean {
  return nodes.some(
    (node) =>
      node.id === board.goal_node_id &&
      node.roles.includes("goal") &&
      !node.roles.includes("choice"),
  );
}
