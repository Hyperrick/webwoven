<script lang="ts">
  let {
    moves,
    par,
    seconds,
    score,
  }: {
    moves: number;
    par: number | null;
    seconds: number;
    score: number | null;
  } = $props();

  const time = $derived(
    `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`,
  );
</script>

<dl class="game-metrics" aria-label="Current route statistics">
  <div>
    <dt>Moves</dt>
    <dd>{moves}</dd>
  </div>
  <div>
    <dt>Par</dt>
    <dd>{par ?? "—"}</dd>
  </div>
  <div>
    <dt>Time</dt>
    <dd>{time}</dd>
  </div>
  <div>
    <dt>Score</dt>
    <dd>{score ?? "—"}</dd>
  </div>
</dl>
