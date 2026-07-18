import type { SessionSnapshot } from "../api/types";
import { hintCount, movesRelativeToPar, trackAnalytics } from "./analytics";

export class RoundLifecycleAnalytics {
  private readonly reportedStarts = new Set<string>();
  private readonly reportedCompletions = new Set<string>();

  reportStarted(snapshot: SessionSnapshot): void {
    if (this.reportedStarts.has(snapshot.id)) return;
    this.reportedStarts.add(snapshot.id);
    trackAnalytics("round_started", {
      mode: snapshot.mode,
      difficulty: snapshot.difficulty,
      category: snapshot.category,
    });
  }

  reportCompleted(snapshot: SessionSnapshot): void {
    if (this.reportedCompletions.has(snapshot.id)) return;
    this.reportedCompletions.add(snapshot.id);
    trackAnalytics("round_completed", {
      mode: snapshot.mode,
      difficulty: snapshot.difficulty,
      category: snapshot.category,
      result: "goal_reached",
      moves_relative_to_par: movesRelativeToPar(
        snapshot.moves,
        snapshot.shortest_distance,
      ),
      hints: hintCount(snapshot.hints_used.length),
    });
  }
}
