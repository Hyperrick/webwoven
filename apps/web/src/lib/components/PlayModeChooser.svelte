<script lang="ts">
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    onSolo,
    onDaily,
    onRelay,
  }: {
    onSolo: () => void;
    onDaily: () => void;
    onRelay: () => void;
  } = $props();

  const modes = [
    {
      id: "solo",
      number: "01",
      title: "Single player",
      description: "Find a route at your own pace.",
      select: () => onSolo(),
    },
    {
      id: "daily",
      number: "02",
      title: "Daily challenge",
      description: "Solve the same route as everyone today.",
      select: () => onDaily(),
    },
    {
      id: "relay",
      number: "03",
      title: "Multiplayer",
      description: "Race live with 2–4 players.",
      select: () => onRelay(),
    },
  ] as const;
</script>

<section class="play-mode-chooser" aria-labelledby="play-mode-title">
  <header class="play-mode-chooser__header">
    <h2 id="play-mode-title">Select play mode</h2>
  </header>

  <div class="play-mode-chooser__options">
    {#each modes as mode}
      <button
        class={`play-mode-card play-mode-card--${mode.id}`}
        type="button"
        onclick={mode.select}
      >
        <span class="play-mode-card__number">{mode.number}</span>
        <span class="play-mode-card__copy">
          <strong>{mode.title}</strong>
          <span>{mode.description}</span>
        </span>
        <span class="play-mode-card__action">
          <AtlasIcon name="arrow" size={20} />
        </span>
      </button>
    {/each}
  </div>
</section>
