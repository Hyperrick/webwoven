<script lang="ts">
  import type { DailyLeaderboard as DailyLeaderboardData } from "../api/types";

  let {
    leaderboard,
    status,
    error,
    onRetry,
    showHeader = true,
  }: {
    leaderboard: DailyLeaderboardData;
    status: "idle" | "loading" | "ready" | "error";
    error: string;
    onRetry: () => void;
    showHeader?: boolean;
  } = $props();

  const currentIsVisible = $derived(
    leaderboard.entries.some((entry) => entry.is_current_guest),
  );
</script>

<div class="leaderboard">
  {#if showHeader}
    <header>
      <h2>Today’s field</h2>
      <span>UTC</span>
    </header>
  {/if}

  {#if status === "loading" || status === "idle"}
    <p class="leaderboard__status" role="status">Reading today’s field…</p>
  {:else if status === "error"}
    <div class="leaderboard__status" role="alert">
      <p>{error || "Today’s field is temporarily unavailable."}</p>
      <button class="secondary-action" type="button" onclick={onRetry}>
        Try again
      </button>
    </div>
  {:else if leaderboard.entries.length === 0}
    <p class="leaderboard__status">No completed routes yet today.</p>
  {:else}
    <ol>
      {#each leaderboard.entries as entry (entry.rank)}
        <li
          class:leaderboard__you={entry.is_current_guest}
          aria-current={entry.is_current_guest ? "true" : undefined}
        >
          <span>{entry.rank}</span>
          <strong>
            {entry.display_name}
            {#if entry.is_current_guest}<em>You</em>{/if}
          </strong>
          <small>{entry.moves} moves · {entry.elapsed_seconds}s</small>
          <b>{entry.score}</b>
        </li>
      {/each}
    </ol>

    {#if leaderboard.current_guest_entry && !currentIsVisible}
      <div class="leaderboard__position">
        <p>Your position</p>
        <div aria-current="true">
          <span>{leaderboard.current_guest_entry.rank}</span>
          <strong
            >{leaderboard.current_guest_entry.display_name}<em>You</em></strong
          >
          <small>
            {leaderboard.current_guest_entry.moves} moves ·
            {leaderboard.current_guest_entry.elapsed_seconds}s
          </small>
          <b>{leaderboard.current_guest_entry.score}</b>
        </div>
      </div>
    {/if}
  {/if}
</div>
