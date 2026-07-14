import type { MapBoardNode, MapBoardNodeRole } from "../domain/map-board";

export type MapNodeTokenState = "current" | "goal" | "trail" | "discarded";

export interface MapNodeTokenPresentation {
  state: MapNodeTokenState;
  radius: number;
}

const TOKEN_RADIUS: Record<MapNodeTokenState, number> = {
  current: 23,
  goal: 20,
  trail: 17.5,
  discarded: 15,
};

/** Resolve the shared semantic token used by both WebGL and SVG adapters. */
export function mapNodeTokenState(
  node: MapBoardNode,
): MapNodeTokenState | null {
  if (hasRole(node, "current")) return "current";
  if (hasRole(node, "discarded")) return "discarded";
  if (hasRole(node, "goal")) return "goal";
  if (hasRole(node, "trail")) return "trail";
  if (hasRole(node, "choice")) return null;
  return "discarded";
}

/** Choice cards own live endpoints; resolved and goal nodes keep tokens. */
export function mapNodeTokenPresentation(
  node: MapBoardNode,
): MapNodeTokenPresentation | null {
  const state = mapNodeTokenState(node);
  return state ? { state, radius: TOKEN_RADIUS[state] } : null;
}

function hasRole(node: MapBoardNode, role: MapBoardNodeRole): boolean {
  return node.roles.includes(role);
}
