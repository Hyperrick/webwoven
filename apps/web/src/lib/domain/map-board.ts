import type { EntitySummary, SessionSnapshot, TrailEntry } from "../api/types";
import { flattenMoveChoices, stableMapIdentity } from "./map-board-choices";
import {
  centerY,
  createMapBoardLayout,
  laneY,
  pointForColumn,
} from "./map-board-layout";
import type {
  MapBoard,
  MapBoardLink,
  MapBoardNode,
  MapBoardNodeRole,
  MapBoardRelation,
  MapBoardTrailVisit,
  MapMoveChoice,
} from "./map-board-model";

export { flattenMoveChoices } from "./map-board-choices";
export type {
  MapBoard,
  MapBoardLayout,
  MapBoardLink,
  MapBoardNode,
  MapBoardNodeRole,
  MapBoardPoint,
  MapBoardRelation,
  MapBoardTrailVisit,
  MapMoveChoice,
  MapMoveConnection,
} from "./map-board-model";

type DecisionStage = NonNullable<SessionSnapshot["decision_history"]>[number];
type DecisionChoice = DecisionStage["choices"][number];

interface ArchivedChoice {
  id: string;
  target: EntitySummary;
  relation: MapBoardRelation;
  statement: string;
  selected: boolean;
}

const ROLE_ORDER: MapBoardNodeRole[] = [
  "start",
  "trail",
  "current",
  "choice",
  "discarded",
  "goal",
];

function visitNodeId(index: number, qid: string): string {
  return `visit:${index}:${qid}`;
}

function optionNodeId(stageIndex: number, choiceId: string): string {
  return `option:${stageIndex}:${stableMapIdentity(choiceId)}`;
}

function goalNodeId(qid: string): string {
  return `goal:${qid}`;
}

function archivedRelation(choice: DecisionChoice): MapBoardRelation {
  return {
    group_id: `${choice.relation.property_id}-${choice.relation.direction}`,
    property_id: choice.relation.property_id,
    label: choice.relation.label,
    direction: choice.relation.direction,
    glyph: choice.relation.glyph,
  };
}

function archivedChoices(
  stage: DecisionStage,
  stageIndex: number,
): ArchivedChoice[] {
  const grouped = new Map<string, DecisionChoice[]>();
  for (const choice of [...stage.choices].sort((left, right) =>
    left.target.qid.localeCompare(right.target.qid, "en"),
  )) {
    const choices = grouped.get(choice.target.qid) ?? [];
    choices.push(choice);
    grouped.set(choice.target.qid, choices);
  }

  return [...grouped.values()].map((connections) => {
    const selectedConnection = connections.find(
      (choice) => choice.id === stage.selected_choice_id,
    );
    const primary = selectedConnection ?? connections[0];
    const selected =
      stage.action === "follow" &&
      (selectedConnection !== undefined ||
        primary.target.qid === stage.destination.qid);
    return {
      id: `history-choice:${stageIndex}:${primary.target.qid}`,
      target: primary.target,
      relation: archivedRelation(primary),
      statement: primary.statement,
      selected,
    };
  });
}

function stagedLiveChoices(
  snapshot: SessionSnapshot,
  stageIndex: number,
  sourceNodeId: string,
): MapMoveChoice[] {
  return flattenMoveChoices(snapshot).map((choice) => ({
    ...choice,
    id: `stage:${stageIndex}:${choice.id}`,
    source_node_id: sourceNodeId,
    target_node_id: optionNodeId(stageIndex, choice.id),
  }));
}

function trailVisits(trail: TrailEntry[]): MapBoardTrailVisit[] {
  const seen = new Set<string>();
  return trail.map((entry, index) => {
    const revisited = seen.has(entry.qid) || entry.revisited === true;
    seen.add(entry.qid);
    return {
      index,
      node_id: visitNodeId(index, entry.qid),
      qid: entry.qid,
      label: entry.label,
      statement: entry.relation,
      revisited,
    };
  });
}

function visitSummaries(snapshot: SessionSnapshot): EntitySummary[] {
  const destinations = (snapshot.decision_history ?? []).map(
    (stage) => stage.destination,
  );
  return snapshot.trail.map((entry, index) => {
    if (index === 0) return snapshot.start;
    const destination = destinations[index - 1];
    if (destination?.qid === entry.qid) return destination;
    if (index === snapshot.trail.length - 1) return snapshot.current;
    return {
      qid: entry.qid,
      label: entry.label,
      description: "A visited entity in this route.",
      category: snapshot.start.category,
      source_kind: "unknown",
    };
  });
}

function roles(...values: MapBoardNodeRole[]): MapBoardNodeRole[] {
  const selected = new Set(values);
  return ROLE_ORDER.filter((role) => selected.has(role));
}

function visitNodes(
  snapshot: SessionSnapshot,
  visits: MapBoardTrailVisit[],
  history: ArchivedChoice[][],
  layout: MapBoard["layout"],
): MapBoardNode[] {
  const summaries = visitSummaries(snapshot);
  return visits.map((visit, index) => {
    const priorChoices = index === 0 ? undefined : history[index - 1];
    const selectedIndex =
      priorChoices?.findIndex((choice) => choice.selected) ?? -1;
    const absoluteY =
      selectedIndex >= 0 ? laneY(selectedIndex, layout) : centerY(layout);
    const nodeRoles: MapBoardNodeRole[] = ["trail"];
    if (index === 0) nodeRoles.push("start");
    if (index === visits.length - 1) nodeRoles.push("current");
    if (visit.qid === snapshot.target.qid) nodeRoles.push("goal");
    return {
      id: visit.node_id,
      qid: visit.qid,
      label: visit.label,
      summary: summaries[index],
      roles: roles(...nodeRoles),
      position: pointForColumn(index, absoluteY, visit.qid, layout),
      choice_ids: [],
      stage_index: index,
    };
  });
}

function archivedNodes(
  snapshot: SessionSnapshot,
  history: ArchivedChoice[][],
  layout: MapBoard["layout"],
): MapBoardNode[] {
  return history.flatMap((choices, stageIndex) =>
    choices.flatMap((choice, laneIndex) => {
      if (choice.selected) return [];
      const id = optionNodeId(stageIndex, choice.id);
      const nodeRoles: MapBoardNodeRole[] = ["discarded"];
      if (choice.target.qid === snapshot.target.qid) nodeRoles.push("goal");
      return [
        {
          id,
          qid: choice.target.qid,
          label: choice.target.label,
          summary: choice.target,
          roles: roles(...nodeRoles),
          position: pointForColumn(
            stageIndex + 1,
            laneY(laneIndex, layout),
            choice.target.qid,
            layout,
          ),
          choice_ids: [choice.id],
          stage_index: stageIndex + 1,
        },
      ];
    }),
  );
}

function activeChoiceNodes(
  snapshot: SessionSnapshot,
  choices: MapMoveChoice[],
  layout: MapBoard["layout"],
): MapBoardNode[] {
  return choices.map((choice, index) => ({
    id: choice.target_node_id,
    qid: choice.target.qid,
    label: choice.target.label,
    summary: choice.target,
    roles: roles(
      "choice",
      ...(choice.target.qid === snapshot.target.qid
        ? (["goal"] as MapBoardNodeRole[])
        : []),
    ),
    position: pointForColumn(
      layout.active_choice_column,
      laneY(index, layout),
      choice.target.qid,
      layout,
    ),
    choice_ids: [choice.id],
    stage_index: layout.active_choice_column,
  }));
}

function goalMarker(
  snapshot: SessionSnapshot,
  currentNodeId: string,
  activeNodes: MapBoardNode[],
  layout: MapBoard["layout"],
): MapBoardNode | undefined {
  if (snapshot.current.qid === snapshot.target.qid) return undefined;
  if (activeNodes.some((node) => node.qid === snapshot.target.qid))
    return undefined;
  return {
    id: goalNodeId(snapshot.target.qid),
    qid: snapshot.target.qid,
    label: snapshot.target.label,
    summary: snapshot.target,
    roles: roles("goal"),
    position: pointForColumn(
      layout.active_choice_column + 1,
      centerY(layout),
      snapshot.target.qid,
      layout,
    ),
    choice_ids: [],
    stage_index: layout.active_choice_column + 1,
  };
}

function buildLinks(
  visits: MapBoardTrailVisit[],
  history: ArchivedChoice[][],
  choices: MapMoveChoice[],
): MapBoardLink[] {
  const trailLinks = visits.slice(1).map((visit, index): MapBoardLink => ({
    id: `trail-link:${index}:${visit.node_id}`,
    kind: "trail",
    source_node_id: visits[index].node_id,
    target_node_id: visit.node_id,
    statement: visit.statement,
  }));
  const discardedLinks = history.flatMap((stageChoices, stageIndex) =>
    stageChoices.flatMap((choice): MapBoardLink[] =>
      choice.selected
        ? []
        : [
            {
              id: `discarded-link:${stageIndex}:${choice.id}`,
              kind: "discarded",
              source_node_id: visits[stageIndex].node_id,
              target_node_id: optionNodeId(stageIndex, choice.id),
              choice_id: choice.id,
              statement: choice.statement,
            },
          ],
    ),
  );
  const liveLinks = choices.map((choice): MapBoardLink => ({
    id: `choice-link:${choice.id}`,
    kind: "choice",
    source_node_id: choice.source_node_id,
    target_node_id: choice.target_node_id,
    choice_id: choice.id,
    statement: choice.statement,
  }));
  return [...trailLinks, ...discardedLinks, ...liveLinks];
}

/** Build the full, ever-widening exploration map from server-owned history. */
export function buildMapBoard(snapshot: SessionSnapshot): MapBoard {
  const visits = trailVisits(snapshot.trail);
  const recordedHistory = (snapshot.decision_history ?? []).map(
    archivedChoices,
  );
  const resolvedStageCount = Math.max(
    recordedHistory.length,
    visits.length - 1,
  );
  const history = Array.from(
    { length: resolvedStageCount },
    (_, index) => recordedHistory[index] ?? [],
  );
  const liveChoiceCount = flattenMoveChoices(snapshot).length;
  const layout = createMapBoardLayout({
    resolvedStageCount,
    laneCounts: [...history.map((choices) => choices.length), liveChoiceCount],
  });
  const currentNodeId =
    visits.at(-1)?.node_id ?? visitNodeId(0, snapshot.current.qid);
  const choices = stagedLiveChoices(
    snapshot,
    layout.current_column,
    currentNodeId,
  );
  const resolvedNodes = visitNodes(snapshot, visits, history, layout);
  const discardedNodes = archivedNodes(snapshot, history, layout);
  const liveNodes = activeChoiceNodes(snapshot, choices, layout);
  const marker = goalMarker(snapshot, currentNodeId, liveNodes, layout);
  const currentGoal =
    resolvedNodes.find(
      (node) => node.id === currentNodeId && node.qid === snapshot.target.qid,
    ) ?? liveNodes.find((node) => node.qid === snapshot.target.qid);
  const nodes = [
    ...resolvedNodes,
    ...discardedNodes,
    ...liveNodes,
    ...(marker ? [marker] : []),
  ].sort(
    (left, right) =>
      left.position.x - right.position.x ||
      left.position.y - right.position.y ||
      left.id.localeCompare(right.id, "en"),
  );

  return {
    start_node_id: visits[0]?.node_id ?? visitNodeId(0, snapshot.start.qid),
    current_node_id: currentNodeId,
    goal_node_id:
      currentGoal?.id ?? marker?.id ?? goalNodeId(snapshot.target.qid),
    nodes,
    links: buildLinks(visits, history, choices),
    choices,
    trail: visits,
    layout,
  };
}
