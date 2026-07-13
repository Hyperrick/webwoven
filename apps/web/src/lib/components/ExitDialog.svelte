<script lang="ts">
  let {
    open,
    onStay,
    onLeave,
  }: { open: boolean; onStay: () => void; onLeave: () => void } = $props();
  let stayButton = $state<HTMLButtonElement>();

  $effect(() => {
    if (open) stayButton?.focus();
  });
</script>

<svelte:window
  onkeydown={(event) => open && event.key === "Escape" && onStay()}
/>

{#if open}
  <div class="modal-scrim" role="presentation">
    <div
      class="exit-dialog"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="exit-title"
      aria-describedby="exit-copy"
    >
      <p class="eyebrow">Leave this route?</p>
      <h2 id="exit-title">Your map is still unfinished.</h2>
      <p id="exit-copy">
        Leaving now abandons this attempt. You can safely retrace a move with
        the in-game Back control.
      </p>
      <div class="exit-dialog__actions">
        <button
          bind:this={stayButton}
          class="primary-action"
          type="button"
          onclick={onStay}>Keep exploring</button
        >
        <button class="text-action" type="button" onclick={onLeave}
          >Leave route</button
        >
      </div>
    </div>
  </div>
{/if}
