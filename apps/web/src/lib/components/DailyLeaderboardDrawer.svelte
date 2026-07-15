<script lang="ts">
  import type { DailyLeaderboard as DailyLeaderboardData } from "../api/types";
  import { trapDialogFocus } from "../a11y/trap-dialog-focus";
  import AtlasIcon from "./AtlasIcon.svelte";
  import DailyLeaderboard from "./DailyLeaderboard.svelte";

  let {
    open,
    leaderboard,
    status,
    error,
    onRetry,
    onClose,
  }: {
    open: boolean;
    leaderboard: DailyLeaderboardData;
    status: "idle" | "loading" | "ready" | "error";
    error: string;
    onRetry: () => void;
    onClose: () => void;
  } = $props();

  let closeButton = $state<HTMLButtonElement>();

  $effect(() => {
    if (!open) return;

    const returnFocusTo =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    closeButton?.focus();

    return () => returnFocusTo?.focus();
  });
</script>

<svelte:window
  onkeydown={(event) => open && event.key === "Escape" && onClose()}
/>

{#if open}
  <button
    class="drawer-scrim"
    type="button"
    aria-label="Close Daily leaderboard"
    onclick={onClose}
  ></button>
  <div
    id="daily-leaderboard-drawer"
    class="drawer leaderboard-drawer"
    role="dialog"
    aria-modal="true"
    aria-labelledby="daily-leaderboard-title"
    use:trapDialogFocus
  >
    <header class="drawer__header">
      <div>
        <p class="eyebrow">Daily leaderboard · UTC</p>
        <h2 id="daily-leaderboard-title">Today’s field</h2>
      </div>
      <button
        bind:this={closeButton}
        class="icon-button"
        type="button"
        onclick={onClose}
        aria-label="Close Daily leaderboard"
      >
        <AtlasIcon name="close" size={20} />
      </button>
    </header>

    <div class="drawer__body leaderboard-drawer__body">
      <DailyLeaderboard
        {leaderboard}
        {status}
        {error}
        {onRetry}
        showHeader={false}
      />
    </div>
  </div>
{/if}
