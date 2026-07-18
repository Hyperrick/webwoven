<script lang="ts">
  type ConfettiShape = "ticket" | "square" | "ribbon";

  interface ConfettiPiece {
    id: number;
    shape: ConfettiShape;
    style: string;
  }

  const COLOR_TOKENS = [
    "--color-signal",
    "--color-ochre",
    "--color-moss",
    "--color-cartographic",
    "--color-sienna",
    "--color-olive",
    "--color-copper",
    "--color-teal",
    "--color-rosewood",
    "--color-atlas-blue",
  ] as const;
  const SHAPES: readonly ConfettiShape[] = ["ticket", "square", "ribbon"];
  const CONFETTI_PIECES = Array.from(
    { length: 72 },
    (_, index): ConfettiPiece => {
      const left = (index * 37 + 7) % 101;
      const delay = (index * 83) % 960;
      const duration = 2_800 + ((index * 97) % 1_500);
      const drift = ((index * 29) % 31) - 15;
      const turn = 520 + ((index * 131) % 980);
      const width = 7 + ((index * 7) % 8);
      const height = 12 + ((index * 11) % 15);

      return {
        id: index,
        shape: SHAPES[index % SHAPES.length],
        style: [
          `--confetti-left: ${left}%`,
          `--confetti-delay: ${delay}ms`,
          `--confetti-duration: ${duration}ms`,
          `--confetti-drift: ${drift}vw`,
          `--confetti-turn: ${turn}deg`,
          `--confetti-width: ${width}px`,
          `--confetti-height: ${height}px`,
          `--confetti-color: var(${COLOR_TOKENS[index % COLOR_TOKENS.length]})`,
        ].join("; "),
      };
    },
  );

  let { sessionId }: { sessionId?: string } = $props();
</script>

{#if sessionId}
  {#key sessionId}
    <div
      class="route-confetti"
      data-route-confetti={sessionId}
      aria-hidden="true"
    >
      {#each CONFETTI_PIECES as piece (piece.id)}
        <span
          class="route-confetti__piece route-confetti__piece--{piece.shape}"
          style={piece.style}
        ></span>
      {/each}
    </div>
  {/key}
{/if}
