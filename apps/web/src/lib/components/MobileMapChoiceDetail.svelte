<script lang="ts">
  import type { MapMoveChoice } from "../domain/map-board";
  import AtlasIcon from "./AtlasIcon.svelte";
  import EndpointArtwork from "./EndpointArtwork.svelte";

  let {
    choice,
    goal = false,
    compassSelecting = false,
    busy = false,
    onConfirm,
    onClose,
  }: {
    choice: MapMoveChoice;
    goal?: boolean;
    compassSelecting?: boolean;
    busy?: boolean;
    onConfirm: (choice: MapMoveChoice) => void;
    onClose: () => void;
  } = $props();

  let actionLabel = $derived(
    compassSelecting
      ? `Check route to ${choice.target.label}`
      : goal
        ? `Finish route to ${choice.target.label}`
        : `Move to ${choice.target.label}`,
  );

  function hintLabel(hint: MapMoveChoice["relation"]["hint"]): string {
    if (hint === "dead_end") return "Dead end";
    if (hint === "longer" || hint === "unlikely") return "Longer route";
    return "Promising route";
  }
</script>

<aside
  id="mobile-map-choice-detail"
  class="mobile-map-choice-detail"
  class:mobile-map-choice-detail--goal={goal}
  data-map-interactive="route-preview"
  data-map-scrollable
  data-mobile-choice-detail
  data-relation-kind={choice.relation.glyph}
  aria-label={`Route details for ${choice.target.label}`}
  aria-live="polite"
>
  <span class="mobile-map-choice-detail__relation" aria-hidden="true">
    <AtlasIcon name={choice.relation.glyph} size={18} />
  </span>
  <div class="mobile-map-choice-detail__copy">
    <small>
      {choice.relation.hint
        ? hintLabel(choice.relation.hint)
        : goal
          ? "Goal in reach"
          : "Route preview"}
    </small>
    <strong>{choice.target.label}</strong>
    <p>{choice.statement}</p>
  </div>
  <EndpointArtwork
    entity={choice.target}
    endpoint={goal ? "goal" : "node"}
    className="mobile-map-choice-detail__artwork"
    loading="eager"
  />
  <button
    type="button"
    class="mobile-map-choice-detail__close"
    data-map-interactive="preview-close"
    aria-label="Close route details"
    onclick={onClose}
  >
    <AtlasIcon name="close" size={16} />
  </button>
  <button
    type="button"
    class="mobile-map-choice-detail__action"
    data-map-interactive="move"
    disabled={busy}
    onclick={() => onConfirm(choice)}
  >
    <span>{actionLabel}</span>
    <AtlasIcon name={compassSelecting ? "compass" : "arrow"} size={18} />
  </button>
</aside>
