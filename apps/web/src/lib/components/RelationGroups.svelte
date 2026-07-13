<script lang="ts">
  import type { RelationGroup } from "../api/types";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    groups,
    disabled = false,
    onFollow,
  }: {
    groups: RelationGroup[];
    disabled?: boolean;
    onFollow: (edgeToken: string) => void;
  } = $props();

  let expanded = $state<string | null>(null);

  $effect(() => {
    groups;
    expanded = groups.length === 1 ? (groups[0]?.property_id ?? null) : null;
  });
</script>

<section class="relation-index" aria-labelledby="relation-title">
  <div class="relation-index__heading">
    <div>
      <p class="eyebrow">Choose a bearing</p>
      <h2 id="relation-title">Known connections</h2>
    </div>
    <p>
      {groups.reduce((total, group) => total + group.edges.length, 0)} possible turns
    </p>
  </div>

  {#if groups.length === 0}
    <p class="empty-bearing">
      This edge of the atlas ends here. Retrace your route to continue.
    </p>
  {:else}
    <div class="relation-index__list">
      {#each groups as group (group.property_id)}
        <article
          class:relation-group--hinted={group.hint === "promising"}
          class="relation-group"
        >
          <button
            type="button"
            class="relation-group__toggle"
            aria-expanded={expanded === group.property_id}
            aria-controls={`relation-${group.property_id}`}
            onclick={() =>
              (expanded =
                expanded === group.property_id ? null : group.property_id)}
          >
            <span class="relation-group__glyph"
              ><AtlasIcon name={group.glyph} size={23} /></span
            >
            <span class="relation-group__label">
              <small
                >{group.direction === "incoming"
                  ? "Connected from"
                  : "Follow relation"}</small
              >
              {group.label}
            </span>
            {#if group.hint}
              <span class="relation-group__hint">{group.hint}</span>
            {/if}
            <span class="relation-group__count">{group.edges.length}</span>
            <span class="relation-group__expand" aria-hidden="true"
              >{expanded === group.property_id ? "−" : "+"}</span
            >
          </button>

          {#if expanded === group.property_id}
            <div
              class="relation-group__edges"
              id={`relation-${group.property_id}`}
            >
              {#each group.edges as edge (edge.edge_token)}
                <button
                  class="edge-choice"
                  type="button"
                  {disabled}
                  onclick={() => onFollow(edge.edge_token)}
                >
                  <span>
                    <strong>{edge.target.label}</strong>
                    <small>{edge.target.description}</small>
                  </span>
                  <AtlasIcon name="arrow" size={21} />
                </button>
              {/each}
            </div>
          {/if}
        </article>
      {/each}
    </div>
  {/if}
</section>
