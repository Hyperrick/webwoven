import type { HintType, RelationGroup, UsedHint } from "../api/types";
import { hintPenalty } from "./scoring";

const BRIDGE_ENTITY = "British Museum";
const PROMISING_ENTITIES = ["Q149116", "Q6373", "Q84", "Q145"];

export function applyHintToGroups(
  groups: RelationGroup[],
  type: HintType,
  selectedPropertyId?: string,
): { groups: RelationGroup[]; hint: UsedHint } {
  if (type === "compass") {
    const selected =
      groups.find((group) => group.property_id === selectedPropertyId) ??
      groups[0];
    const promising = selected?.edges.some((edge) =>
      PROMISING_ENTITIES.includes(edge.target.qid),
    );
    const message = selected
      ? `The “${selected.label}” bearing looks ${promising ? "promising" : "unlikely"}.`
      : "There is no bearing to evaluate here.";
    return {
      groups: groups.map((group) =>
        group.property_id === selected?.property_id
          ? { ...group, hint: promising ? "promising" : "unlikely" }
          : group,
      ),
      hint: { type, penalty: hintPenalty(type), message },
    };
  }

  if (type === "lens") {
    const promisingIndex = groups.findIndex((group) =>
      group.edges.some((edge) => PROMISING_ENTITIES.includes(edge.target.qid)),
    );
    return {
      groups: groups.map((group, index) =>
        index === promisingIndex ? { ...group, hint: "promising" } : group,
      ),
      hint: {
        type,
        penalty: hintPenalty(type),
        message:
          "The Cartographer has marked a relation on a near-optimal route.",
      },
    };
  }

  return {
    groups,
    hint: {
      type,
      penalty: hintPenalty(type),
      message: `A fragment of the route names ${BRIDGE_ENTITY} as a possible bridge.`,
    },
  };
}
