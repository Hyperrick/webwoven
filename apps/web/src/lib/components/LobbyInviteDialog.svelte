<script lang="ts">
  import type { RoomInvitePreview } from "../api/types";

  let {
    invite,
    busy = false,
    onJoin,
    onCancel,
  }: {
    invite?: RoomInvitePreview;
    busy?: boolean;
    onJoin: () => void;
    onCancel: () => void;
  } = $props();

  let joinButton = $state<HTMLButtonElement>();
  const canOpen = $derived(
    invite?.is_member ||
      (invite?.joinable && invite.player_count < invite.max_players),
  );

  $effect(() => {
    if (invite) joinButton?.focus();
  });
</script>

<svelte:window
  onkeydown={(event) => invite && event.key === "Escape" && onCancel()}
/>

{#if invite}
  <div class="modal-scrim" role="presentation">
    <div
      class="exit-dialog lobby-invite-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="lobby-invite-title"
      aria-describedby="lobby-invite-copy"
    >
      <p class="eyebrow">Relay lobby · {invite.code}</p>
      <h2 id="lobby-invite-title">
        {invite.host_display_name} invited you.
      </h2>
      <p id="lobby-invite-copy">
        {#if invite.is_member}
          You already belong to this lobby. Open it in this Webwoven window?
        {:else if !invite.joinable}
          This lobby is no longer accepting explorers.
        {:else if invite.player_count >= invite.max_players}
          This lobby already has four explorers.
        {:else}
          Join {invite.player_count} of {invite.max_players} explorers before the
          host starts the route?
        {/if}
      </p>
      <div class="exit-dialog__actions">
        {#if canOpen}
          <button
            bind:this={joinButton}
            class="primary-action"
            type="button"
            disabled={busy}
            onclick={onJoin}
          >
            {invite.is_member ? "Open lobby" : "Join lobby"}
          </button>
        {/if}
        <button
          class="text-action"
          type="button"
          disabled={busy}
          onclick={onCancel}
        >
          Not now
        </button>
      </div>
    </div>
  </div>
{/if}
