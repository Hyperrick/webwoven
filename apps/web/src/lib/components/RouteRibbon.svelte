<script lang="ts">
  import type { EntitySummary, TrailEntry } from "../api/types";
  import AtlasIcon from "./AtlasIcon.svelte";

  let { trail, target }: { trail: TrailEntry[]; target: EntitySummary } =
    $props();
</script>

<section class="route-ribbon" aria-label="Your route so far">
  <div class="section-label">
    <AtlasIcon name="route" size={15} /> Route ribbon
  </div>
  <ol class="route-ribbon__track">
    {#each trail as item, index (`${index}:${item.qid}`)}
      <li
        class:route-ribbon__item--revisited={item.revisited}
        class="route-ribbon__item"
      >
        <span class="route-ribbon__number"
          >{String(index + 1).padStart(2, "0")}</span
        >
        <span>{item.label}</span>
      </li>
    {/each}
    <li class="route-ribbon__target">
      <span class="route-ribbon__number">GOAL</span>
      <span>{target.label}</span>
    </li>
  </ol>
</section>
