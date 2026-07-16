import type { EntitySummary, SessionSnapshot } from "../api/types";

export function trailEntityAt(
  session: SessionSnapshot,
  index: number,
): EntitySummary | undefined {
  const entry = session.trail[index];
  if (!entry) return undefined;
  if (entry.summary) return entry.summary;
  if (index === 0 && entry.qid === session.start.qid) return session.start;
  const decision = session.decision_history?.[index - 1]?.destination;
  if (decision?.qid === entry.qid) return decision;
  if (index === session.trail.length - 1 && entry.qid === session.target.qid)
    return session.target;
  if (entry.qid === session.current.qid) return session.current;
  return session.navigation_stack?.find((entity) => entity.qid === entry.qid);
}

export function sessionMediaEntities(
  session: SessionSnapshot,
): EntitySummary[] {
  const entities = [
    session.start,
    session.target,
    session.current,
    ...(session.navigation_stack ?? []),
    ...session.trail.flatMap((_, index) => {
      const entity = trailEntityAt(session, index);
      return entity ? [entity] : [];
    }),
    ...(session.decision_history ?? []).flatMap((stage) => [
      stage.source,
      stage.destination,
      ...stage.choices.map((choice) => choice.target),
    ]),
    ...session.relation_groups.flatMap((group) =>
      group.edges.map((edge) => edge.target),
    ),
  ];
  return [...new Map(entities.map((entity) => [entity.qid, entity])).values()];
}
