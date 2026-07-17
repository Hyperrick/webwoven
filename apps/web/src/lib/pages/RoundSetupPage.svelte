<script lang="ts">
  import type { Difficulty, RoundFilters } from "../api/types";
  import AtlasIcon from "../components/AtlasIcon.svelte";
  import CategoryPicker from "../components/CategoryPicker.svelte";
  import DifficultyPicker from "../components/DifficultyPicker.svelte";
  import {
    loadCategoryFilter,
    persistCategoryFilter,
    roundFilters,
  } from "../round-setup/category-filter";
  import { loadDifficulty, persistDifficulty } from "../round-setup/difficulty";

  let {
    busy = false,
    onConfirm,
  }: {
    busy?: boolean;
    onConfirm: (filters: RoundFilters) => void;
  } = $props();

  let difficulty = $state<Difficulty>(loadDifficulty("solo"));
  let category = $state(loadCategoryFilter("solo"));

  function confirm(): void {
    persistDifficulty("solo", difficulty);
    persistCategoryFilter("solo", category);
    onConfirm(roundFilters(difficulty, category));
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
        Choose a topic or leave the whole atlas open. The endpoints stay sealed
        until the route is revealed.
      </p>
    </div>

    <div class="round-setup__form">
      <CategoryPicker
        id="solo-category"
        bind:value={category}
        disabled={busy}
      />
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
