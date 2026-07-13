<script lang="ts">
  import type { HintType, RelationGroup, UsedHint } from "../api/types";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    groups,
    used,
    disabled = false,
    onHint,
  }: {
    groups: RelationGroup[];
    used: UsedHint[];
    disabled?: boolean;
    onHint: (type: HintType, propertyId?: string) => void;
  } = $props();

  const hintUsed = (type: HintType) => used.some((hint) => hint.type === type);
  let latest = $derived(used.at(-1));
</script>

<aside class="hint-dock" aria-labelledby="hint-title">
  <div>
    <p class="eyebrow">The Cartographer’s desk</p>
    <h2 id="hint-title">Need a bearing?</h2>
  </div>
  <div class="hint-dock__actions">
    <button
      type="button"
      aria-label="Use Compass hint for a 75 point penalty"
      disabled={disabled || hintUsed("compass") || groups.length === 0}
      onclick={() => onHint("compass", groups[0]?.property_id)}
    >
      <AtlasIcon name="compass" size={21} />
      <span><strong>Compass</strong><small>Test a relation · −75</small></span>
    </button>
    <button
      type="button"
      aria-label="Use Lens hint for a 150 point penalty"
      disabled={disabled || hintUsed("lens")}
      onclick={() => onHint("lens")}
    >
      <AtlasIcon name="lens" size={21} />
      <span><strong>Lens</strong><small>Mark a bearing · −150</small></span>
    </button>
    <button
      type="button"
      aria-label="Use Map Fragment hint for a 250 point penalty"
      disabled={disabled || hintUsed("map_fragment")}
      onclick={() => onHint("map_fragment")}
    >
      <AtlasIcon name="map" size={21} />
      <span
        ><strong>Map fragment</strong><small>Reveal a bridge · −250</small
        ></span
      >
    </button>
  </div>
  {#if latest}
    <p class="cartographer-note" role="status">“{latest.message}”</p>
  {/if}
</aside>
