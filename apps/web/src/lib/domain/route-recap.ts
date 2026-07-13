import type { SessionSnapshot } from "../api/types";

type RecapSession = Pick<
  SessionSnapshot,
  "start" | "target" | "trail" | "moves"
>;

export function routeRecap(session: RecapSession): string {
  const intermediates = session.trail
    .slice(1, -1)
    .map((item) => item.label)
    .filter((label, index, labels) => labels.indexOf(label) === index);
  const routeDetail = intermediateSummary(intermediates);
  const moveLabel = session.moves === 1 ? "move" : "moves";

  return `You connected ${session.start.label} to ${session.target.label} in ${session.moves} ${moveLabel}${routeDetail}.`;
}

function intermediateSummary(labels: string[]): string {
  if (labels.length === 0) return "";
  if (labels.length === 1) return `, passing through ${labels[0]}`;
  if (labels.length === 2) {
    return `, passing through ${labels[0]} and ${labels[1]}`;
  }
  return `, passing through ${labels[0]}, ${labels[1]}, and ${labels.length - 2} more`;
}
