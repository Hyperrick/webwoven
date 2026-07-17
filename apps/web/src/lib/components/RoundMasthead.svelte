<script lang="ts">
  import AtlasIcon from "./AtlasIcon.svelte";
  import GameMetrics from "./GameMetrics.svelte";

  let {
    startLabel,
    targetLabel,
    modeLabel,
    difficulty = "Normal",
    moves,
    par,
    seconds,
    score,
    canGoBack,
    busy = false,
    onBack,
  }: {
    startLabel: string;
    targetLabel: string;
    modeLabel: string;
    difficulty?: "Easy" | "Normal" | "Hard";
    moves: number;
    par: number | null;
    seconds: number;
    score: number | null;
    canGoBack: boolean;
    busy?: boolean;
    onBack: () => void;
  } = $props();
</script>

<section class="round-masthead" aria-labelledby="round-objective">
  <h1 id="round-objective" class="round-masthead__context">
    Reach {targetLabel} from {startLabel}
  </h1>

  <div class="round-masthead__identity">
    <p
      class="round-masthead__state"
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <span class="round-masthead__marker" aria-hidden="true"></span>
      <strong>
        <span class="round-masthead__state-full">Round active</span>
        <span class="round-masthead__state-short" aria-hidden="true">Live</span>
      </strong>
      <span class="round-masthead__timer-context">Timer running</span>
    </p>
    <p class="round-masthead__meta">
      {modeLabel}<span aria-hidden="true">·</span>{difficulty} difficulty
    </p>
  </div>

  <GameMetrics {moves} {par} {seconds} {score} />

  <button
    class="back-action"
    type="button"
    aria-label="In-game Back"
    disabled={busy || !canGoBack}
    onclick={onBack}
  >
    <AtlasIcon name="back" size={17} /> <span>Back</span><kbd>B</kbd>
  </button>
</section>
