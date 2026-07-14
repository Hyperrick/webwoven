<script lang="ts">
  import { tick } from "svelte";
  import type { MapNodeInspection } from "../domain/map-inspection";
  import "../../styles/map-inspector.css";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    inspection,
    onClose,
  }: {
    inspection: MapNodeInspection | null;
    onClose: () => void;
  } = $props();

  let closeButton = $state<HTMLButtonElement>();
  let returnFocus = $state<HTMLElement | null>(null);
  let openNodeId = $state<string | null>(null);
  let focusRequest = 0;

  $effect(() => {
    const nodeId = inspection?.node_id;
    if (!nodeId) {
      openNodeId = null;
      return;
    }
    if (!openNodeId && document.activeElement instanceof HTMLElement)
      returnFocus = document.activeElement;
    openNodeId = nodeId;
    const request = ++focusRequest;
    void tick().then(() => {
      if (request === focusRequest) closeButton?.focus({ preventScroll: true });
    });
  });

  function handleKeydown(event: KeyboardEvent): void {
    if (inspection && event.key === "Escape") {
      event.preventDefault();
      closeInspector();
    }
  }

  function closeInspector(): void {
    const target = returnFocus;
    returnFocus = null;
    onClose();
    void tick().then(() => {
      if (target?.isConnected) target.focus({ preventScroll: true });
    });
  }

  function statusLabel(status: MapNodeInspection["status"]): string {
    if (status === "current") return "Current position";
    if (status === "taken") return "Route taken";
    return "Route not taken";
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if inspection}
  <div
    class="map-inspector"
    class:map-inspector--current={inspection.status === "current"}
    class:map-inspector--taken={inspection.status === "taken"}
    class:map-inspector--not-taken={inspection.status === "not_taken"}
    role="dialog"
    aria-modal="false"
    aria-labelledby="map-inspector-title"
    data-map-inspector
    data-map-interactive="inspector"
    data-map-scrollable
  >
    <header class="map-inspector__header">
      <div>
        <p class="map-inspector__status">
          {statusLabel(inspection.status)}
        </p>
        <h3 id="map-inspector-title">{inspection.label}</h3>
        <small>{inspection.qid}</small>
      </div>
      <button
        type="button"
        class="map-inspector__close"
        data-map-interactive="inspect-close"
        aria-label="Close entity details"
        onclick={closeInspector}
        bind:this={closeButton}
      >
        <AtlasIcon name="close" size={18} />
      </button>
    </header>

    <p class="map-inspector__description">{inspection.description}</p>

    <section
      class="map-inspector__connections"
      aria-labelledby="map-connections-title"
    >
      <h4 id="map-connections-title">How it connects</h4>
      {#if inspection.connections.length > 0}
        <ol>
          {#each inspection.connections as connection (connection.link_id)}
            <li>
              <p class="map-inspector__route">
                <strong>{connection.source.label}</strong>
                <span aria-hidden="true">→</span>
                <span class="map-inspector__to">to</span>
                <strong>{connection.target.label}</strong>
              </p>
              {#if connection.statements.length > 0}
                <ul class="map-inspector__statements">
                  {#each connection.statements as statement (statement)}
                    <li>{statement}</li>
                  {/each}
                </ul>
              {:else}
                <p class="map-inspector__empty">
                  No relationship statement is stored for this connection.
                </p>
              {/if}
            </li>
          {/each}
        </ol>
      {:else}
        <p class="map-inspector__empty">
          No incoming connection is stored for this node.
        </p>
      {/if}
    </section>
  </div>
{/if}
