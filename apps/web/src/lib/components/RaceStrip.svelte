<script lang="ts">
  import type { RelayConnectionState } from "../api/room-event-stream";
  import type { RoomSnapshot } from "../api/types";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    room,
    currentMoves,
    connection = "connected",
  }: {
    room: RoomSnapshot;
    currentMoves: number;
    connection?: RelayConnectionState;
  } = $props();

  const progressFor = (isCurrent: boolean | undefined, moves: number) => {
    if (isCurrent)
      return currentMoves >= 4
        ? "arrived"
        : currentMoves >= 2
          ? "closing-in"
          : "mapping";
    return moves >= 4 ? "arrived" : moves >= 2 ? "closing-in" : "mapping";
  };
</script>

<section class="race-strip" aria-labelledby="race-status-title">
  <div class="race-strip__title">
    <AtlasIcon name="users" size={17} />
    <div>
      <h2 id="race-status-title">Live relay · {room.code}</h2>
      <span class="race-strip__connection race-strip__connection--{connection}">
        {connection === "connected" ? "Live" : connection}
      </span>
    </div>
  </div>
  <ol>
    {#each room.players as player, index (player.id)}
      <li class:race-strip__player--you={player.is_current_guest}>
        <span class="race-strip__place">{index + 1}</span>
        <span
          ><strong>{player.display_name}</strong><small
            >{progressFor(player.is_current_guest, player.moves)} · {player.is_current_guest
              ? currentMoves
              : player.moves} moves</small
          ></span
        >
      </li>
    {/each}
  </ol>
</section>
