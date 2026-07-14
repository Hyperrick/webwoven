import type { MapBoardLayout, MapBoardPoint } from "./map-board-model";

const MINIMUM_WIDTH_UNITS = 88;
const MINIMUM_HEIGHT_UNITS = 38;
const LEFT_GUTTER_UNITS = 14;
const RIGHT_GUTTER_UNITS = 22;
// A full lane must clear the widest move card and the centered goal label.
// Thirty rem leaves a deliberate visual gutter without relying on CSS nudges.
const COLUMN_GAP_UNITS = 30;
const CHOICE_TOP_UNITS = 12;
const CHOICE_LANE_GAP_UNITS = 10;
const BOTTOM_CLEARANCE_UNITS = 10;

export interface MapBoardLayoutInput {
  resolvedStageCount: number;
  laneCounts: number[];
}

export function createMapBoardLayout({
  resolvedStageCount,
  laneCounts,
}: MapBoardLayoutInput): MapBoardLayout {
  const choiceLaneCount = Math.max(0, ...laneCounts);
  const occupiedChoiceHeight =
    choiceLaneCount === 0
      ? 0
      : CHOICE_TOP_UNITS +
        (choiceLaneCount - 1) * CHOICE_LANE_GAP_UNITS +
        BOTTOM_CLEARANCE_UNITS;
  const currentColumn = resolvedStageCount;
  const activeChoiceColumn = currentColumn + 1;
  const width = Math.max(
    MINIMUM_WIDTH_UNITS,
    LEFT_GUTTER_UNITS +
      (activeChoiceColumn + 1) * COLUMN_GAP_UNITS +
      RIGHT_GUTTER_UNITS,
  );

  return {
    width_units: width,
    height_units: Math.max(MINIMUM_HEIGHT_UNITS, occupiedChoiceHeight),
    minimum_width_units: MINIMUM_WIDTH_UNITS,
    minimum_height_units: MINIMUM_HEIGHT_UNITS,
    column_gap_units: COLUMN_GAP_UNITS,
    choice_top_units: CHOICE_TOP_UNITS,
    choice_lane_gap_units: CHOICE_LANE_GAP_UNITS,
    bottom_clearance_units: BOTTOM_CLEARANCE_UNITS,
    choice_lane_count: choiceLaneCount,
    current_column: currentColumn,
    active_choice_column: activeChoiceColumn,
  };
}

export function pointForColumn(
  column: number,
  absoluteY: number,
  qid: string,
  layout: MapBoardLayout,
): MapBoardPoint {
  return {
    x: (LEFT_GUTTER_UNITS + column * COLUMN_GAP_UNITS) / layout.width_units,
    y: absoluteY / layout.height_units,
    z: depthFor(`${column}:${qid}`),
  };
}

export function laneY(index: number, layout: MapBoardLayout): number {
  return layout.choice_top_units + index * layout.choice_lane_gap_units;
}

export function centerY(layout: MapBoardLayout): number {
  return layout.height_units / 2;
}

function depthFor(identity: string): number {
  const bucket = Number.parseInt(stableHash(identity).slice(-2), 36) % 5;
  return 0.46 + bucket * 0.02;
}

function stableHash(value: string): string {
  let hash = 0x811c9dc5;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(36);
}
