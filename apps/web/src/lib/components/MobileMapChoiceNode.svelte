<script lang="ts">
  import type { MapMoveChoice } from "../domain/map-board";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    choice,
    positionStyle,
    selected = false,
    busy = false,
    goal = false,
    nearFocus = false,
    hintLabel,
    ariaLabel,
    confirmIcon = "arrow",
    onActivate,
  }: {
    choice: MapMoveChoice;
    positionStyle: string;
    selected?: boolean;
    busy?: boolean;
    goal?: boolean;
    nearFocus?: boolean;
    hintLabel?: string;
    ariaLabel: string;
    confirmIcon?: "arrow" | "compass";
    onActivate: (choice: MapMoveChoice) => void;
  } = $props();
</script>

<button
  type="button"
  class:map-choice--promising={choice.relation.hint === "promising"}
  class:map-choice--longer={choice.relation.hint === "longer" ||
    choice.relation.hint === "unlikely"}
  class:map-choice--dead-end={choice.relation.hint === "dead_end"}
  class:mobile-map-choice-node--selected={selected}
  class:mobile-map-choice-node--goal={goal}
  class="map-choice mobile-map-choice-node"
  style={positionStyle}
  disabled={busy}
  data-map-node
  data-map-node-id={choice.target_node_id}
  data-map-focus="choice"
  data-map-near-focus={nearFocus ? "choice" : undefined}
  data-map-interactive={selected ? "move" : "preview"}
  data-mobile-choice-node
  data-relation-kind={choice.relation.glyph}
  aria-label={ariaLabel}
  aria-pressed={selected}
  aria-expanded={selected}
  aria-controls={selected ? "mobile-map-choice-detail" : undefined}
  onclick={() => onActivate(choice)}
>
  <span class="mobile-map-choice-node__marker" aria-hidden="true">
    <AtlasIcon name={choice.relation.glyph} size={18} />
  </span>
  {#if selected}
    <span
      class="mobile-map-choice-node__confirm"
      data-mobile-choice-confirm
      aria-hidden="true"
    >
      <AtlasIcon name={confirmIcon} size={14} />
    </span>
  {/if}
  <strong class="mobile-map-choice-node__label">{choice.target.label}</strong>
  {#if hintLabel}
    <small class="map-choice__hint">{hintLabel}</small>
  {/if}
</button>
