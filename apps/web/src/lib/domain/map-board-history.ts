import type {
  DecisionChoice,
  DecisionConnection,
  DecisionRelation,
  DecisionStage,
  EntitySummary,
  TrailEntry,
} from "../api/types";
import type {
  MapBoardConnection,
  MapBoardRelation,
  MapBoardTrailVisit,
} from "./map-board-model";

export interface ArchivedChoice {
  id: string;
  target: EntitySummary;
  relation: MapBoardRelation;
  statement: string;
  connections: MapBoardConnection[];
  selected: boolean;
}

export interface ArchivedStage {
  action: DecisionStage["action"];
  destination: EntitySummary;
  choices: ArchivedChoice[];
}

export function visitNodeId(index: number, qid: string): string {
  return `visit:${index}:${qid}`;
}

function relationFor(relation: DecisionRelation): MapBoardRelation {
  return {
    group_id: `${relation.property_id}-${relation.direction}`,
    property_id: relation.property_id,
    label: relation.label,
    direction: relation.direction,
    glyph: relation.glyph,
  };
}

function mapConnection(connection: DecisionConnection): MapBoardConnection {
  return {
    id: connection.id,
    relation: relationFor(connection.relation),
    statement: connection.statement,
  };
}

function connectionsFor(choice: DecisionChoice): MapBoardConnection[] {
  if (choice.connections !== undefined && choice.connections.length > 0) {
    return choice.connections.map(mapConnection);
  }
  return [
    mapConnection({
      id: choice.id,
      relation: choice.relation,
      statement: choice.statement,
    }),
  ];
}

function uniqueConnections(
  choices: readonly DecisionChoice[],
): MapBoardConnection[] {
  const seen = new Set<string>();
  return choices.flatMap(connectionsFor).filter((connection) => {
    if (seen.has(connection.id)) return false;
    seen.add(connection.id);
    return true;
  });
}

function compareChoices(left: DecisionChoice, right: DecisionChoice): number {
  return (
    left.target.qid.localeCompare(right.target.qid, "en") ||
    left.id.localeCompare(right.id, "en") ||
    left.statement.localeCompare(right.statement, "en")
  );
}

function archiveStage(stage: DecisionStage, stageIndex: number): ArchivedStage {
  const grouped = new Map<string, DecisionChoice[]>();
  for (const choice of [...stage.choices].sort(compareChoices)) {
    const choices = grouped.get(choice.target.qid) ?? [];
    choices.push(choice);
    grouped.set(choice.target.qid, choices);
  }

  const choices = [...grouped.values()].flatMap(
    (targetChoices): ArchivedChoice[] => {
      const selectedChoice = targetChoices.find(
        (choice) => choice.id === stage.selected_choice_id,
      );
      const primary = selectedChoice ?? targetChoices[0];
      const selected =
        stage.action === "follow" &&
        (selectedChoice !== undefined ||
          primary.target.qid === stage.destination.qid);

      // Back returns through the navigation stack, not through this visible edge.
      // Keeping the matching frontier option would duplicate the return visit.
      if (
        stage.action === "back" &&
        primary.target.qid === stage.destination.qid
      ) {
        return [];
      }

      return [
        {
          id: `history-choice:${stageIndex}:${primary.target.qid}`,
          target: primary.target,
          relation: relationFor(primary.relation),
          statement: primary.statement,
          connections: uniqueConnections(targetChoices),
          selected,
        },
      ];
    },
  );
  return { action: stage.action, destination: stage.destination, choices };
}

export function archiveDecisionHistory(
  history: readonly DecisionStage[] = [],
): ArchivedStage[] {
  return history.map(archiveStage);
}

function matchingStage(
  history: readonly ArchivedStage[],
  visitIndex: number,
  entry: TrailEntry,
): ArchivedStage | undefined {
  const stage = history[visitIndex - 1];
  return stage?.destination.qid === entry.qid ? stage : undefined;
}

function selectedChoice(stage: ArchivedStage): ArchivedChoice | undefined {
  return stage.choices.find((choice) => choice.selected);
}

function historicalStatement(stage: ArchivedStage): string | undefined {
  if (stage.action === "back") return `Returned to ${stage.destination.label}.`;
  return selectedChoice(stage)?.statement;
}

/** Rebuild durable incoming-link semantics even when wire trail entries are terse. */
export function buildTrailVisits(
  trail: readonly TrailEntry[],
  history: readonly ArchivedStage[],
): MapBoardTrailVisit[] {
  const seen = new Set<string>();
  return trail.map((entry, index) => {
    const stage =
      index === 0 ? undefined : matchingStage(history, index, entry);
    const traversed =
      stage?.action === "follow" ? selectedChoice(stage) : undefined;
    const statement = stage
      ? (historicalStatement(stage) ?? entry.relation)
      : entry.relation;
    const revisited =
      seen.has(entry.qid) ||
      entry.revisited === true ||
      stage?.action === "back";
    seen.add(entry.qid);
    return {
      index,
      node_id: visitNodeId(index, entry.qid),
      qid: entry.qid,
      label: entry.label,
      ...(statement === undefined ? {} : { statement }),
      revisited,
      ...(stage === undefined ? {} : { action: stage.action }),
      connections: traversed?.connections ?? [],
    };
  });
}
