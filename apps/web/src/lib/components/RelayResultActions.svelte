<script lang="ts">
  import { onMount } from "svelte";
  import type { RoomSnapshot } from "../api/types";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    room,
    busy = false,
    onVote,
    onRefresh,
    onLobby,
    onSolo,
  }: {
    room?: RoomSnapshot;
    busy?: boolean;
    onVote: (accept: boolean) => void;
    onRefresh: () => void;
    onLobby: () => void;
    onSolo: () => void;
  } = $props();

  let now = $state(Date.now());
  let refreshedDeadline = $state("");
  let currentPlayer = $derived(
    room?.players.find((player) => player.is_current_guest),
  );
  let activePlayers = $derived(
    room?.players.filter((player) => player.active) ?? [],
  );
  let acceptedCount = $derived(
    activePlayers.filter((player) => player.rematch_vote === true).length,
  );
  let graceSeconds = $derived(remainingSeconds(room?.grace_ends_at, now));
  let rematchSeconds = $derived(remainingSeconds(room?.rematch_ends_at, now));

  onMount(() => {
    const interval = window.setInterval(() => (now = Date.now()), 250);
    return () => window.clearInterval(interval);
  });

  $effect(() => {
    const deadline =
      room?.state === "grace_period"
        ? room.grace_ends_at
        : room?.state === "finished"
          ? room.rematch_ends_at
          : undefined;
    if (!deadline || deadline === refreshedDeadline) return;
    if (remainingSeconds(deadline, now) !== 0) return;
    refreshedDeadline = deadline;
    onRefresh();
  });

  function remainingSeconds(
    deadline: string | undefined,
    current: number,
  ): number | null {
    if (!deadline) return null;
    const end = Date.parse(deadline);
    if (!Number.isFinite(end)) return null;
    return Math.max(0, Math.ceil((end - current) / 1_000));
  }

  function clock(seconds: number | null): string {
    if (seconds === null) return "00:00";
    return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
  }
</script>

<div class="next-route relay-result-actions">
  <p class="eyebrow">Multiplayer</p>

  {#if !room}
    <h2>Keep racing together.</h2>
    <p>Return to multiplayer to create or join a lobby.</p>
    <button class="primary-action" type="button" onclick={onLobby}>
      Browse lobbies <AtlasIcon name="arrow" size={20} />
    </button>
  {:else if room.state === "closed" && room.close_reason === "not_enough_players"}
    <h2>Not enough players found.</h2>
    <p>
      Fewer than two explorers chose another round, so this lobby is closed.
    </p>
    <div class="next-route__actions">
      <button class="primary-action" type="button" onclick={onLobby}>
        Find another lobby <AtlasIcon name="arrow" size={20} />
      </button>
      <button class="text-action" type="button" onclick={onSolo}
        >Play a Solo route</button
      >
    </div>
  {:else if currentPlayer && !currentPlayer.active}
    <h2>You left this lobby.</h2>
    <p>The explorers who voted yes are starting their next shared route.</p>
    <button class="primary-action" type="button" onclick={onLobby}>
      Find another lobby <AtlasIcon name="arrow" size={20} />
    </button>
  {:else if room.state === "grace_period" || room.state === "racing"}
    <h2>The field is still racing.</h2>
    <p>
      The first finish is recorded. Everyone else has
      <strong class="relay-result-actions__clock" role="timer">
        {clock(graceSeconds)}
      </strong>
      to reach {room.target.label}.
    </p>
  {:else if room.state === "finished"}
    <h2>Race another round?</h2>
    <p>
      At least two explorers must say yes within
      <strong class="relay-result-actions__clock" role="timer">
        {clock(rematchSeconds)}
      </strong>. The next route keeps this lobby and code.
    </p>
    <p class="relay-result-actions__votes" role="status">
      {acceptedCount} of {activePlayers.length} ready for another round
    </p>
    {#if currentPlayer?.rematch_vote === true}
      <p class="relay-result-actions__decision">
        You said yes. Waiting for the lobby.
      </p>
    {:else if currentPlayer?.rematch_vote === false}
      <p class="relay-result-actions__decision">
        You chose to leave after this round.
      </p>
    {:else}
      <div class="next-route__actions">
        <button
          class="primary-action"
          type="button"
          disabled={busy || rematchSeconds === 0}
          onclick={() => onVote(true)}
        >
          Yes, race again <AtlasIcon name="arrow" size={20} />
        </button>
        <button
          class="text-action"
          type="button"
          disabled={busy || rematchSeconds === 0}
          onclick={() => onVote(false)}
        >
          No, leave lobby
        </button>
      </div>
    {/if}
  {:else}
    <h2>The next route is opening.</h2>
    <p>Everyone who voted yes will enter the same synchronized countdown.</p>
  {/if}
</div>
