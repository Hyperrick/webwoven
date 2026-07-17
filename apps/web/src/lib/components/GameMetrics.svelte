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

<dl class="game-metrics" aria-label="Current round statistics" aria-live="off">
  <div>
    <dt>Time</dt>
    <dd>{time}</dd>
  </div>
  <div>
    <dt>Moves</dt>
    <dd>{moves}</dd>
  </div>
  <div>
    <dt>Par</dt>
    <dd>{par ?? "Unknown"}</dd>
  </div>
  <div>
    <dt>Score</dt>
    <dd class:game-metrics__pending={score === null}>
      {#if score === null}
        <span class="game-metrics__pending-full">At finish</span>
        <span class="game-metrics__pending-short" aria-hidden="true">—</span>
      {:else}
        {score}
      {/if}
    </dd>
  </div>
</dl>
