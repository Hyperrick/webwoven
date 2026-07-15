<script lang="ts">
  import { tick } from "svelte";
  import type { Guest } from "../api/types";
  import GuestNameForm from "./GuestNameForm.svelte";

  let {
    open,
    guest,
    busy,
    error,
    onSave,
    onKeep,
    onCancel,
  }: {
    open: boolean;
    guest?: Guest;
    busy: boolean;
    error: string;
    onSave: (name: string) => void;
    onKeep: () => void;
    onCancel: () => void;
  } = $props();

  let dialog = $state<HTMLDivElement>();

  $effect(() => {
    if (open) void tick().then(() => dialog?.querySelector("input")?.focus());
  });

  function continueWith(name: string): void {
    if (name === guest?.display_name) {
      onKeep();
      return;
    }
    onSave(name);
  }
</script>

<svelte:window
  onkeydown={(event) => open && !busy && event.key === "Escape" && onCancel()}
/>

{#if open && guest}
  <button
    class="drawer-scrim"
    type="button"
    aria-label="Cancel explorer name"
    onclick={() => !busy && onCancel()}
  ></button>
  <div
    bind:this={dialog}
    class="guest-name-prompt"
    role="dialog"
    aria-modal="true"
    aria-labelledby="guest-name-title"
  >
    <p class="eyebrow">Before you join the field</p>
    <h2 id="guest-name-title">What should other explorers call you?</h2>
    <p>
      Keep this generated name or type your own. It stays with this browser—no
      registration, password, or cross-device account.
    </p>
    <GuestNameForm
      {guest}
      {busy}
      {error}
      submitLabel="Continue"
      inputId="guest-name-prompt-input"
      onSubmit={continueWith}
    />
    <button
      class="secondary-action guest-name-prompt__cancel"
      type="button"
      disabled={busy}
      onclick={onCancel}
    >
      Not now
    </button>
  </div>
{/if}
