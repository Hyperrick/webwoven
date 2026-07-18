<script lang="ts">
  import type { RelayConnectionState } from "../api/room-event-stream";
  import type { RoomPlayer, RoomSnapshot } from "../api/types";
  import {
    formatRelayGrace,
    relayGraceRemainingSeconds,
  } from "../domain/relay-grace";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    room,
    currentMoves,
    connection = "connected",
    now = Date.now(),
  }: {
    room: RoomSnapshot;
    currentMoves: number;
    connection?: RelayConnectionState;
    now?: number;
  } = $props();

  let graceSeconds = $derived(relayGraceRemainingSeconds(room, now));
  let activePlayers = $derived(room.players.filter((player) => player.active));
  let finishedCount = $derived(
    activePlayers.filter(
      (player) => player.progress === "arrived" || finishRank(player) !== null,
    ).length,
  );

  function finishRank(player: RoomPlayer): number | null {
    const value = player.finish_rank;
    return typeof value === "number" && Number.isInteger(value) && value > 0
      ? value
      : null;
  }

  function progressLabel(player: RoomPlayer): string {
    const rank = finishRank(player);
    if (rank !== null) return `finished #${rank}`;
    if (player.progress === "arrived") return "finished";
    return player.progress === "closing-in" ? "closing in" : "mapping";
  }
</script>

<section
  class="race-strip"
  aria-labelledby="race-status-title"
  data-room-state={room.state}
>
  <div class="race-strip__title">
    <AtlasIcon name="users" size={17} />
    <div>
      <h2 id="race-status-title">
        <span class="race-strip__mode-full">Live relay</span>
        <span class="race-strip__mode-short">Relay</span>
        · {room.code}
      </h2>
      {#if graceSeconds !== null}
        <span class="race-strip__desktop-grace">
          {#if graceSeconds > 0}
            Final chance ·
            <strong
              role="timer"
              aria-label={`${graceSeconds} seconds remaining in the relay`}
              >{formatRelayGrace(graceSeconds)}</strong
            >
          {:else}
            Race ending…
          {/if}
        </span>
      {:else}
        <span
          class="race-strip__connection race-strip__connection--{connection}"
        >
          {connection === "connected" ? "Live" : connection}
        </span>
      {/if}
    </div>
  </div>

  <p class="race-strip__mobile-summary">
    {#if graceSeconds !== null}
      {#if graceSeconds > 0}
        <span>Final chance</span>
        <strong
          class="race-strip__grace"
          role="timer"
          aria-label={`${graceSeconds} seconds remaining in the relay`}
          >{formatRelayGrace(graceSeconds)}</strong
        >
      {:else}
        <strong>Race ending…</strong>
      {/if}
    {:else if room.state === "finished" || room.state === "closed"}
      <strong>Race complete</strong>
    {:else}
      <strong>{activePlayers.length} players</strong>
      {#if finishedCount > 0}<span>· {finishedCount} finished</span>{/if}
    {/if}
  </p>

  <ol class="race-strip__roster">
    {#each activePlayers as player, index (player.id)}
      <li class:race-strip__player--you={player.is_current_guest}>
        <span class="race-strip__place">{finishRank(player) ?? index + 1}</span>
        <span
          ><strong>{player.display_name}</strong><small
            >{progressLabel(player)} · {player.is_current_guest
              ? currentMoves
              : player.moves} moves</small
          ></span
        >
      </li>
    {/each}
  </ol>
</section>
