<script lang="ts">
  import type { EntitySummary } from "../api/types";
  import { endpointArtworkFor } from "../domain/endpoint-artwork";

  let {
    entity,
    endpoint,
    className = "",
    loading = "lazy",
    fit = "cover",
  }: {
    entity: EntitySummary;
    endpoint: "start" | "goal" | "node";
    className?: string;
    loading?: "eager" | "lazy";
    fit?: "cover" | "contain";
  } = $props();

  const artwork = $derived(endpointArtworkFor(entity));
</script>

<span
  class={`endpoint-artwork endpoint-artwork--${endpoint} endpoint-artwork--fit-${fit} ${className}`.trim()}
  data-endpoint-artwork={endpoint}
  data-image-kind={artwork.kind}
  aria-hidden="true"
>
  {#if fit === "contain"}
    <img
      class="endpoint-artwork__backdrop"
      src={artwork.src}
      alt=""
      {loading}
      decoding="async"
    />
  {/if}
  <img
    class="endpoint-artwork__image"
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
