<script lang="ts">
  import { tick } from "svelte";
  import { shareLobbyInvite } from "../sharing/lobby-invite";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    code,
    hostDisplayName,
    shareable = false,
  }: {
    code: string;
    hostDisplayName: string;
    shareable?: boolean;
  } = $props();

  let sharing = $state(false);
  let feedback = $state("");
  let manualUrl = $state("");
  let manualInput = $state<HTMLInputElement>();

  async function shareLobby(): Promise<void> {
    sharing = true;
    feedback = "";
    manualUrl = "";
    try {
      const result = await shareLobbyInvite({ code, hostDisplayName });
      if (result.status === "shared") feedback = "Invitation shared.";
      if (result.status === "copied") feedback = "Invite link copied.";
      if (result.status === "manual") {
        manualUrl = result.url;
        feedback = "Copy this invite link:";
        await tick();
        manualInput?.focus();
        manualInput?.select();
      }
    } finally {
      sharing = false;
    }
  }
</script>

<div class="lobby-code-share">
  <div class="room-code" aria-label={`Lobby code ${code}`}>
    <span>Lobby code</span>
    <strong>{code}</strong>
  </div>
  {#if shareable}
    <button
      class="lobby-code-share__button"
      type="button"
      disabled={sharing}
      aria-label={`Share lobby ${code}`}
      onclick={() => void shareLobby()}
    >
      <AtlasIcon name="share" size={20} />
      <span>{sharing ? "Opening…" : "Share"}</span>
    </button>
  {/if}
  {#if feedback}
    <p class="lobby-code-share__feedback" role="status">{feedback}</p>
  {/if}
  {#if manualUrl}
    <input
      bind:this={manualInput}
      class="lobby-code-share__manual"
      aria-label="Lobby invite link"
      value={manualUrl}
      readonly
      onclick={(event) => event.currentTarget.select()}
    />
  {/if}
</div>
