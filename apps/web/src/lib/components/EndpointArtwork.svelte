<script lang="ts">
  import type { EntitySummary } from "../api/types";
  import { endpointArtworkFor } from "../domain/endpoint-artwork";

  let {
    entity,
    endpoint,
    className = "",
    loading = "lazy",
  }: {
    entity: EntitySummary;
    endpoint: "start" | "goal" | "node";
    className?: string;
    loading?: "eager" | "lazy";
  } = $props();

  const artwork = $derived(endpointArtworkFor(entity));
</script>

<span
  class={`endpoint-artwork endpoint-artwork--${endpoint} ${className}`.trim()}
  data-endpoint-artwork={endpoint}
  data-image-kind={artwork.kind}
  aria-hidden="true"
>
  <img
    src={artwork.src}
    alt=""
    {loading}
    decoding="async"
    fetchpriority={loading === "eager" ? "high" : "auto"}
  />
  {#if artwork.kind === "category"}
    <small class="endpoint-artwork__kind">Category plate</small>
  {/if}
</span>
