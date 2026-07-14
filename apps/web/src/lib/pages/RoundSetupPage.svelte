<script lang="ts">
  import type { Difficulty } from "../api/types";
  import AtlasIcon from "../components/AtlasIcon.svelte";
  import DifficultyPicker from "../components/DifficultyPicker.svelte";
  import { loadDifficulty, persistDifficulty } from "../round-setup/difficulty";

  let {
    busy = false,
    onConfirm,
  }: {
    busy?: boolean;
    onConfirm: (difficulty: Difficulty) => void;
  } = $props();

  let difficulty = $state<Difficulty>(loadDifficulty("solo"));

  function confirm(): void {
    persistDifficulty("solo", difficulty);
    onConfirm(difficulty);
  }
</script>

<main class="round-setup-page">
  <section class="round-setup" aria-labelledby="round-setup-title">
    <div class="round-setup__intro">
      <p class="eyebrow">New solo route</p>
      <h1 id="round-setup-title">
        Set the depth<br /><em>of the expedition.</em>
      </h1>
      <p>
        The category and endpoints stay sealed until the atlas opens. Confirm a
        difficulty for this round.
      </p>
    </div>

    <div class="round-setup__form">
      <DifficultyPicker bind:value={difficulty} disabled={busy} />
      <button
        class="primary-action round-setup__confirm"
        type="button"
        disabled={busy}
        onclick={confirm}
      >
        {busy ? "Preparing atlas…" : "Confirm and reveal"}
        <AtlasIcon name="arrow" size={20} />
      </button>
      <p class="round-setup__note">
        Your last choice is remembered, but every new route waits for your
        confirmation.
      </p>
    </div>
  </section>
</main>
