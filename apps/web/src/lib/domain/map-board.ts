import type { EntitySummary, SessionSnapshot } from "../api/types";
import { flattenMoveChoices, stableMapIdentity } from "./map-board-choices";
import {
  archiveDecisionHistory,
  buildTrailVisits,
  visitNodeId,
} from "./map-board-history";
import type { ArchivedChoice } from "./map-board-history";
import {
  centerY,
  createMapBoardLayout,
  laneY,
  pointForColumn,
  pointForDistantGoal,
} from "./map-board-layout";
import type {
  MapBoard,
  MapBoardLink,
  MapBoardNode,
  MapBoardNodeRole,
  MapBoardTrailVisit,
  MapMoveChoice,
} from "./map-board-model";

export { flattenMoveChoices } from "./map-board-choices";
export type {
  MapBoard,
  MapBoardConnection,
  MapBoardLayout,
  MapBoardLink,
  MapBoardMoveAction,
  MapBoardNode,
  MapBoardNodeRole,
  MapBoardPoint,
  MapBoardRelation,
  MapBoardTrailVisit,
  MapMoveChoice,
  MapMoveConnection,
} from "./map-board-model";

const ROLE_ORDER: MapBoardNodeRole[] = [
  "start",
  "trail",
  "current",
  "choice",
  "discarded",
  "goal",
];

function optionNodeId(stageIndex: number, choiceId: string): string {
  return `option:${stageIndex}:${stableMapIdentity(choiceId)}`;
}

function goalNodeId(qid: string): string {
  return `goal:${qid}`;
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

function visitSummaries(
  snapshot: SessionSnapshot,
  visits: MapBoardTrailVisit[],
  activeStages: NonNullable<SessionSnapshot["decision_history"]>,
): EntitySummary[] {
  const destinations = activeStages.map((stage) => stage.destination);
  return visits.map((entry, index) => {
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
  activeStages: NonNullable<SessionSnapshot["decision_history"]>,
  history: ArchivedChoice[][],
  layout: MapBoard["layout"],
): MapBoardNode[] {
  const summaries = visitSummaries(snapshot, visits, activeStages);
  return visits.map((visit, index) => {
    const priorChoices = index === 0 ? undefined : history[index - 1];
    const selectedIndex =
      priorChoices?.findIndex((choice) => choice.selected) ?? -1;
    const absoluteY =
      selectedIndex >= 0 ? laneY(selectedIndex, layout) : centerY(layout);
    const wasBacktracked = visits[index + 1]?.action === "back";
    const nodeRoles: MapBoardNodeRole[] = wasBacktracked
      ? ["discarded"]
      : ["trail"];
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

function collapsesDeadEnd(
  stage: NonNullable<SessionSnapshot["decision_history"]>[number] | undefined,
): boolean {
  return stage?.action === "back" && stage.choices.length === 0;
}

function spatialDecisionStages(
  stages: NonNullable<SessionSnapshot["decision_history"]>,
): NonNullable<SessionSnapshot["decision_history"]> {
  const active: NonNullable<SessionSnapshot["decision_history"]> = [];
  for (const stage of stages) {
    if (collapsesDeadEnd(stage)) active.pop();
    else active.push(stage);
  }
  return active;
}

function spatialTrailVisits(
  visits: MapBoardTrailVisit[],
  stages: NonNullable<SessionSnapshot["decision_history"]>,
): MapBoardTrailVisit[] {
  const active: MapBoardTrailVisit[] = [];
  for (const visit of visits) {
    const stage = visit.index === 0 ? undefined : stages[visit.index - 1];
    if (collapsesDeadEnd(stage)) active.pop();
    else active.push(visit);
  }
  return active.map((visit, index) => ({
    ...visit,
    index,
    node_id: visitNodeId(index, visit.qid),
  }));
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
    position: pointForDistantGoal(centerY(layout), snapshot.target.qid, layout),
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
    connections: visit.connections,
    ...(visit.action === undefined ? {} : { action: visit.action }),
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
              connections: choice.connections,
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
    connections: choice.connections,
  }));
  return [...trailLinks, ...discardedLinks, ...liveLinks];
}

/** Build the full, ever-widening exploration map from server-owned history. */
export function buildMapBoard(snapshot: SessionSnapshot): MapBoard {
  const archivedStages = archiveDecisionHistory(snapshot.decision_history);
  const trail = buildTrailVisits(snapshot.trail, archivedStages);
  const recordedHistory = archivedStages.map((stage) => stage.choices);
  const activeStages = spatialDecisionStages(snapshot.decision_history ?? []);
  const activeArchivedStages = archiveDecisionHistory(activeStages);
  const activeHistory = activeArchivedStages.map((stage) => stage.choices);
  const visits = spatialTrailVisits(trail, snapshot.decision_history ?? []);
  const resolvedStageCount = Math.max(recordedHistory.length, trail.length - 1);
  const liveChoiceCount = flattenMoveChoices(snapshot).length;
  const layout = createMapBoardLayout({
    resolvedStageCount,
    currentColumn: Math.max(0, visits.length - 1),
    laneCounts: [
      ...recordedHistory.map((choices) => choices.length),
      liveChoiceCount,
    ],
  });
  const currentNodeId =
    visits.at(-1)?.node_id ?? visitNodeId(0, snapshot.current.qid);
  const choices = stagedLiveChoices(
    snapshot,
    layout.current_column,
    currentNodeId,
  );
  const resolvedNodes = visitNodes(
    snapshot,
    visits,
    activeStages,
    activeHistory,
    layout,
  );
  const discardedNodes = archivedNodes(snapshot, activeHistory, layout);
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
    links: buildLinks(visits, activeHistory, choices),
    choices,
    trail,
    layout,
  };
}
