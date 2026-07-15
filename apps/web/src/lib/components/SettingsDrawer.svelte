<script lang="ts">
  import type { Guest } from "../api/types";
  import type { Preferences } from "../preferences/preferences";
  import AtlasIcon from "./AtlasIcon.svelte";
  import GuestNameForm from "./GuestNameForm.svelte";

  let {
    open,
    guest,
    preferences,
    nameBusy,
    nameError,
    nameDisabled,
    onChange,
    onNameSave,
    onClose,
  }: {
    open: boolean;
    guest?: Guest;
    preferences: Preferences;
    nameBusy: boolean;
    nameError: string;
    nameDisabled: boolean;
    onChange: (next: Preferences) => void;
    onNameSave: (name: string) => void;
    onClose: () => void;
  } = $props();

  let closeButton = $state<HTMLButtonElement>();

  $effect(() => {
    if (open) closeButton?.focus();
  });
</script>

<svelte:window
  onkeydown={(event) => open && event.key === "Escape" && onClose()}
/>

{#if open}
  <button
    class="drawer-scrim"
    type="button"
    aria-label="Close settings"
    onclick={onClose}
  ></button>
  <div
    class="drawer"
    role="dialog"
    aria-modal="true"
    aria-labelledby="settings-title"
  >
    <header class="drawer__header">
      <div>
        <p class="eyebrow">Your field kit</p>
        <h2 id="settings-title">Settings</h2>
      </div>
      <button
        bind:this={closeButton}
        class="icon-button"
        type="button"
        onclick={onClose}
        aria-label="Close settings"
      >
        <AtlasIcon name="close" size={20} />
      </button>
    </header>

    <div class="drawer__body settings-list">
      {#if guest}
        <section class="settings-profile" aria-labelledby="profile-name-title">
          <h3 id="profile-name-title">Explorer identity</h3>
          <GuestNameForm
            {guest}
            busy={nameBusy}
            disabled={nameDisabled}
            error={nameError}
            inputId="settings-display-name"
            onSubmit={onNameSave}
          />
          {#if nameDisabled}
            <p class="settings-profile__locked">
              Your name is locked during a live Relay so every participant sees
              the same room roster. Change it after leaving the room.
            </p>
          {/if}
        </section>
      {/if}
      <label class="setting-row">
        <span
          ><strong>Reduce motion</strong><small
            >Use immediate transitions throughout the atlas.</small
          ></span
        >
        <input
          type="checkbox"
          checked={preferences.reducedMotion}
          onchange={(event) =>
            onChange({
              ...preferences,
              reducedMotion: event.currentTarget.checked,
            })}
        />
      </label>
      <label class="setting-row">
        <span
          ><strong>Interface sound</strong><small
            >Play quiet cues for moves and discoveries.</small
          ></span
        >
        <input
          type="checkbox"
          checked={preferences.sound}
          onchange={(event) =>
            onChange({ ...preferences, sound: event.currentTarget.checked })}
        />
      </label>

      <section class="keyboard-map" aria-labelledby="keyboard-title">
        <h3 id="keyboard-title">Keyboard map</h3>
        <p><kbd>Tab</kbd><span>Move between bearings</span></p>
        <p><kbd>← ↑ ↓ →</kbd><span>Pan the exploration map</span></p>
        <p><kbd>+ −</kbd><span>Zoom the exploration map</span></p>
        <p><kbd>0</kbd><span>Fit the explored map</span></p>
        <p><kbd>Home</kbd><span>Return to the current marker</span></p>
        <p><kbd>B</kbd><span>Retrace one step in-game</span></p>
        <p><kbd>Esc</kbd><span>Close an open sheet</span></p>
      </section>
    </div>
  </div>
{/if}
