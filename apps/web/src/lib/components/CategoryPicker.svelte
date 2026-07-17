<script lang="ts">
  import {
    ANY_CATEGORY,
    CATEGORY_FILTER_OPTIONS,
    type CategoryFilter,
  } from "../round-setup/category-filter";

  let {
    id,
    value = $bindable(ANY_CATEGORY),
    disabled = false,
  }: {
    id: string;
    value?: CategoryFilter;
    disabled?: boolean;
  } = $props();
</script>

<div class="category-picker">
  <label for={id}>Route category</label>
  <select {id} bind:value {disabled}>
    <option value={ANY_CATEGORY}>Any category</option>
    {#each CATEGORY_FILTER_OPTIONS as option (option.value)}
      <option value={option.value}>{option.label}</option>
    {/each}
  </select>
  <small>Start and goal share the topic; connections may cross the atlas.</small
  >
</div>
