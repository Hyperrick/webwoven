<script lang="ts">
  import type { EntitySummary } from "../api/types";
  import EntityMark from "./EntityMark.svelte";

  let { entity, target = false }: { entity: EntitySummary; target?: boolean } =
    $props();
</script>

<section
  class:entity-stage--target={target}
  class="entity-stage"
  aria-labelledby={`entity-${entity.qid}`}
>
  <div class="entity-stage__visual">
    <EntityMark category={entity.category} label={entity.label} />
  </div>
  <div class="entity-stage__copy">
    <p class="entity-stage__category">
      {target ? "Destination" : entity.category.replace("_", " & ")}
    </p>
    <h1 id={`entity-${entity.qid}`}>{entity.label}</h1>
    <p class="entity-stage__description">{entity.description}</p>
    {#if entity.fact}
      <p class="entity-stage__fact"><span>Field note</span>{entity.fact}</p>
    {/if}
  </div>
</section>
