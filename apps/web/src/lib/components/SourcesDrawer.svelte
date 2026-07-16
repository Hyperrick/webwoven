<script lang="ts">
  import type { EntitySummary } from "../api/types";
  import { trapDialogFocus } from "../a11y/trap-dialog-focus";
  import {
    provenanceFor,
    verifiedWikidataUrlFor,
  } from "../domain/entity-provenance";
  import { imageAttributionsFor } from "../domain/image-attribution";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    open,
    entity,
    roundEntities = [],
    graphBuild,
    onClose,
    onReport,
  }: {
    open: boolean;
    entity?: EntitySummary;
    roundEntities?: readonly EntitySummary[];
    graphBuild: string;
    onClose: () => void;
    onReport: () => void;
  } = $props();

  let closeButton = $state<HTMLButtonElement>();
  let provenance = $derived(provenanceFor(entity));
  let verifiedWikidataUrl = $derived(
    entity ? verifiedWikidataUrlFor(entity) : undefined,
  );
  let imageAttributions = $derived(
    imageAttributionsFor([entity, ...roundEntities]),
  );
  $effect(() => {
    if (!open) return;

    const returnFocusTo =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    closeButton?.focus();

    return () => returnFocusTo?.focus();
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
    use:trapDialogFocus
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
          <p class="source-ledger__index">{provenance.entityIndexLabel}</p>
          <h3>{entity.label}</h3>
          <p>{entity.description}</p>
          {#if provenance.notice}<p>{provenance.notice}</p>{/if}
          {#if verifiedWikidataUrl}
            <a
              class="text-link"
              href={verifiedWikidataUrl}
              target="_blank"
              rel="noreferrer"
            >
              Open Wikidata record <AtlasIcon name="arrow" size={17} />
            </a>
          {/if}
        </section>
      {:else}
        <section>
          <p class="source-ledger__index">{provenance.entityIndexLabel}</p>
          <h3>Grounded, named connections</h3>
          <p>
            Active gameplay uses an immutable, verified graph bundle. Synthetic
            fixtures are available only to explicitly configured automated
            tests.
          </p>
        </section>
      {/if}

      {#if imageAttributions.length > 0}
        <section class="source-ledger__media-credit">
          <p class="source-ledger__index">
            {imageAttributions.length === 1
              ? "Image credit"
              : "Round image credits"}
          </p>
          {#each imageAttributions as imageAttribution (imageAttribution.sourceUrl)}
            <div class="source-ledger__media-item">
              <p>
                <strong>{imageAttribution.entityLabel}</strong> ·
                {imageAttribution.attributionText}
              </p>
              {#if imageAttribution.contextLabel}
                <p>
                  Documentary context: this image depicts
                  <strong>{imageAttribution.contextLabel}</strong>.
                </p>
              {/if}
              <p class="source-ledger__media-links">
                <a
                  class="text-link"
                  href={imageAttribution.sourceUrl}
                  target="_blank"
                  rel="noreferrer"
                  title={imageAttribution.fileName}
                  aria-label={`View ${imageAttribution.fileName} on Wikimedia Commons`}
                >
                  Wikimedia Commons <AtlasIcon name="arrow" size={17} />
                </a>
                <a
                  class="text-link"
                  href={imageAttribution.licenseUrl}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={`Read ${imageAttribution.licenseLabel} terms`}
                >
                  {imageAttribution.licenseLabel}
                  <AtlasIcon name="arrow" size={17} />
                </a>
              </p>
            </div>
          {/each}
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
          <dt>Knowledge source</dt>
          <dd>{provenance.knowledgeSource}</dd>
        </div>
        <div>
          <dt>Knowledge license</dt>
          <dd>{provenance.knowledgeLicense}</dd>
        </div>
        <div>
          <dt>Review state</dt>
          <dd>{provenance.reviewState}</dd>
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
