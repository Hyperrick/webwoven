<script lang="ts">
  import type { Guest } from "../api/types";
  import {
    guestNameError,
    normalizeGuestName,
  } from "../guest-profile/guest-name";

  let {
    guest,
    busy = false,
    disabled = false,
    error = "",
    submitLabel = "Save name",
    inputId = "guest-display-name",
    onSubmit,
  }: {
    guest: Guest;
    busy?: boolean;
    disabled?: boolean;
    error?: string;
    submitLabel?: string;
    inputId?: string;
    onSubmit: (name: string) => void;
  } = $props();

  let draft = $state("");
  let validation = $state("");

  $effect(() => {
    draft = guest.display_name;
    validation = "";
  });

  function submit(): void {
    const problem = guestNameError(draft);
    if (problem) {
      validation = problem;
      return;
    }
    validation = "";
    onSubmit(normalizeGuestName(draft));
  }
</script>

<form
  class="guest-name-form"
  onsubmit={(event) => {
    event.preventDefault();
    submit();
  }}
>
  <label for={inputId}>Public explorer name</label>
  <p id={`${inputId}-help`}>
    Shown in Daily rankings and multiplayer lobbies. No email or account is
    attached.
  </p>
  <input
    id={inputId}
    name="display-name"
    type="text"
    autocomplete="nickname"
    minlength="2"
    aria-describedby={`${inputId}-help ${inputId}-error`}
    aria-invalid={Boolean(validation || error)}
    bind:value={draft}
    {disabled}
  />
  <p class="guest-name-form__error" id={`${inputId}-error`} aria-live="polite">
    {validation || error}
  </p>
  <button class="primary-action" type="submit" disabled={disabled || busy}>
    {busy ? "Saving…" : submitLabel}
  </button>
</form>
