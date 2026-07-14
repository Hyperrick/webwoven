<script lang="ts">
  import type { Difficulty } from "../api/types";
  import { DIFFICULTIES } from "../round-setup/difficulty";

  let {
    value = $bindable("normal"),
    legend = "Choose difficulty",
    disabled = false,
  }: {
    value?: Difficulty;
    legend?: string;
    disabled?: boolean;
  } = $props();
</script>

<fieldset class="difficulty-picker" {disabled}>
  <legend>{legend}</legend>
  <div class="difficulty-picker__options">
    {#each DIFFICULTIES as option (option.value)}
      <label class:difficulty-picker__option--selected={value === option.value}>
        <input type="radio" bind:group={value} value={option.value} />
        <span>
          <strong>{option.label}</strong>
          <small>{option.note}</small>
        </span>
      </label>
    {/each}
  </div>
</fieldset>
