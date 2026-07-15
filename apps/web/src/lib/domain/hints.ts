import type {
  HintMarker,
  HintOutcome,
  HintType,
  RelationGroup,
  UsedHint,
} from "../api/types";
import { hintPenalty } from "./scoring";

interface HintContext {
  selectedPropertyId?: string;
  selectedEntityQid?: string;
  distanceToTarget: (entityQid: string) => number | null;
}

interface Candidate {
  group: RelationGroup;
  edge: RelationGroup["edges"][number];
  distance: number | null;
}

export function applyHintToGroups(
  groups: RelationGroup[],
  type: HintType,
  context: HintContext,
): { groups: RelationGroup[]; hint: UsedHint } {
  const candidates = groups.flatMap((group) =>
    group.edges.map((edge) => ({
      group,
      edge,
      distance: context.distanceToTarget(edge.target.qid),
    })),
  );
  const reachable = candidates.filter(
    (candidate): candidate is Candidate & { distance: number } =>
      candidate.distance !== null,
  );
  const best = [...reachable].sort(compareCandidates)[0];

  if (type === "compass") {
    const selected = candidates.find(
      ({ group, edge }) =>
        group.property_id === context.selectedPropertyId &&
        edge.target.qid === context.selectedEntityQid,
    );
    if (!selected) throw new Error("Choose a specific route for the Compass.");
    const outcome: HintOutcome =
      selected.distance === null
        ? "dead_end"
        : selected.distance === best?.distance
          ? "promising"
          : "longer";
    return exactResult(
      groups,
      type,
      selected,
      outcome,
      compassMessage(selected.edge.target.label, outcome),
    );
  }

  if (!best) {
    return {
      groups,
      hint: {
        type,
        penalty: hintPenalty(type),
        message: "No grounded hint is available from this entity.",
      },
    };
  }

  const message =
    type === "lens"
      ? `Lens: ${best.edge.target.label} is on a near-optimal route.`
      : `Map Fragment: ${best.edge.target.label} is a valid bridge ahead.`;
  return exactResult(groups, type, best, "promising", message);
}

function exactResult(
  groups: RelationGroup[],
  type: HintType,
  candidate: Candidate,
  outcome: HintOutcome,
  message: string,
): { groups: RelationGroup[]; hint: UsedHint } {
  return {
    groups: markExactEdge(
      groups,
      candidate.group.property_id,
      candidate.edge.target.qid,
      outcome,
    ),
    hint: {
      type,
      penalty: hintPenalty(type),
      message,
      relation_property_id: candidate.group.property_id,
      entity_qid: candidate.edge.target.qid,
      outcome,
    },
  };
}

function markExactEdge(
  groups: RelationGroup[],
  propertyId: string,
  entityQid: string,
  hint: HintMarker,
): RelationGroup[] {
  return groups.map((group) => ({
    ...group,
    edges: group.edges.map((edge) =>
      group.property_id === propertyId && edge.target.qid === entityQid
        ? { ...edge, hint }
        : edge,
    ),
  }));
}

function compareCandidates(
  left: Candidate & { distance: number },
  right: Candidate & { distance: number },
): number {
  return (
    left.distance - right.distance ||
    left.group.property_id.localeCompare(right.group.property_id) ||
    left.edge.target.qid.localeCompare(right.edge.target.qid)
  );
}

function compassMessage(label: string, outcome: HintOutcome): string {
  if (outcome === "dead_end")
    return `Compass: ${label} is a dead end from here.`;
  if (outcome === "longer") return `Compass: ${label} takes a longer route.`;
  return `Compass: ${label} is a promising route.`;
}
