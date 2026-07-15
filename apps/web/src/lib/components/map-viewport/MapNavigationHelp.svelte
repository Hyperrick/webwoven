<script lang="ts">
  let open = $state(false);
</script>

<div class="map-navigation-help">
  <button
    class="map-navigation-help__trigger"
    type="button"
    aria-label="Map controls help"
    aria-expanded={open}
    aria-controls="map-navigation-help-panel"
    title="Map controls help"
    onclick={() => (open = !open)}
  >
    ?
  </button>
  {#if open}
    <div
      id="map-navigation-help-panel"
      class="map-navigation-help__panel"
      role="note"
      aria-label="Map controls"
    >
      <strong>Navigate the map</strong>
      <p>Drag to pan. Pinch or scroll to zoom.</p>
      <ul>
        <li><kbd>Arrows</kbd><span>Pan</span></li>
        <li><kbd>+ / −</kbd><span>Zoom</span></li>
        <li><kbd>0</kbd><span>Fit map</span></li>
        <li><kbd>Home</kbd><span>Return to current</span></li>
      </ul>
    </div>
  {/if}
</div>
