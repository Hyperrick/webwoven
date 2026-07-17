import type { MapBoard } from "./map-board";

export function mapBackTargetNodeId(
  board: Pick<MapBoard, "current_node_id" | "links">,
): string | null {
  return (
    board.links.find(
      (link) =>
        link.kind === "trail" && link.target_node_id === board.current_node_id,
    )?.source_node_id ?? null
  );
}
