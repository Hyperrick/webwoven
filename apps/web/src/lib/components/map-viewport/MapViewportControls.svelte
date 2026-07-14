<script lang="ts">
  import AtlasIcon from "../AtlasIcon.svelte";

  let {
    zoom,
    minimumZoom,
    maximumZoom,
    onZoomOut,
    onZoomIn,
    onFitMap,
    onFocusCurrent,
  }: {
    zoom: number;
    minimumZoom: number;
    maximumZoom: number;
    onZoomOut: () => void;
    onZoomIn: () => void;
    onFitMap: () => void;
    onFocusCurrent: () => void;
  } = $props();
</script>

<div
  class="map-viewport-controls"
  role="toolbar"
  aria-label="Map view"
  data-map-interactive="controls"
>
  <button
    type="button"
    data-map-interactive
    aria-label="Zoom out"
    title="Zoom out (-)"
    disabled={zoom <= minimumZoom}
    onclick={onZoomOut}
  >
    <AtlasIcon name="minus" size={18} />
  </button>
  <output aria-label="Map zoom">{Math.round(zoom * 100)}%</output>
  <button
    type="button"
    data-map-interactive
    aria-label="Zoom in"
    title="Zoom in (+)"
    disabled={zoom >= maximumZoom}
    onclick={onZoomIn}
  >
    <AtlasIcon name="plus" size={18} />
  </button>
  <span class="map-viewport-controls__divider" aria-hidden="true"></span>
  <button
    type="button"
    class="map-viewport-controls__labelled"
    data-map-interactive
    title="Show the entire explored map (0)"
    onclick={onFitMap}
  >
    <AtlasIcon name="map" size={17} />
    Fit map
  </button>
  <button
    type="button"
    class="map-viewport-controls__labelled"
    data-map-interactive
    title="Return to the current position (Home)"
    onclick={onFocusCurrent}
  >
    <AtlasIcon name="focus" size={17} />
    Current
  </button>
</div>
