<script lang="ts">
  import type { EntitySummary } from "../api/types";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    open,
    entity,
    graphBuild,
    onClose,
    onReport,
  }: {
    open: boolean;
    entity?: EntitySummary;
    graphBuild: string;
    onClose: () => void;
    onReport: () => void;
  } = $props();

  let closeButton = $state<HTMLButtonElement>();
  $effect(() => {
    if (open) closeButton?.focus();
  });
</script>

<svelte:window
  onkeydown={(event) => open && event.key === "Escape" && onClose()}
/>

{#if open}
  <button
    class="drawer-scrim"
    type="button"
    aria-label="Close sources"
    onclick={onClose}
  ></button>
  <div
    class="drawer"
    role="dialog"
    aria-modal="true"
    aria-labelledby="sources-title"
  >
    <header class="drawer__header">
      <div>
        <p class="eyebrow">Provenance ledger</p>
        <h2 id="sources-title">Sources</h2>
      </div>
      <button
        bind:this={closeButton}
        class="icon-button"
        type="button"
        onclick={onClose}
        aria-label="Close sources"
      >
        <AtlasIcon name="close" size={20} />
      </button>
    </header>

    <div class="drawer__body source-ledger">
      {#if entity}
        <section>
          <p class="source-ledger__index">Current entity · {entity.qid}</p>
          <h3>{entity.label}</h3>
          <p>{entity.description}</p>
          {#if entity.source_url}
            <a
              class="text-link"
              href={entity.source_url}
              target="_blank"
              rel="noreferrer"
            >
              Open Wikidata record <AtlasIcon name="arrow" size={17} />
            </a>
          {/if}
        </section>
      {:else}
        <section>
          <p class="source-ledger__index">Open knowledge</p>
          <h3>Grounded, named connections</h3>
          <p>
            Every playable link is compiled from a reviewed Wikidata statement
            before release.
          </p>
        </section>
      {/if}

      <dl class="provenance-list">
        <div>
          <dt>Graph build</dt>
          <dd>{graphBuild}</dd>
        </div>
        <div>
          <dt>Runtime lookups</dt>
          <dd>None</dd>
        </div>
        <div>
          <dt>Knowledge license</dt>
          <dd>CC0</dd>
        </div>
        <div>
          <dt>Review state</dt>
          <dd>Curated fixture</dd>
        </div>
      </dl>

      {#if entity}
        <button class="secondary-action" type="button" onclick={onReport}
          >Report unclear or incorrect content</button
        >
      {/if}
    </div>
  </div>
{/if}
