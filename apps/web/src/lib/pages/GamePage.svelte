<script lang="ts">
  import { onMount } from "svelte";
  import type { RelayConnectionState } from "../api/room-event-stream";
  import type { HintType, RoomSnapshot, SessionSnapshot } from "../api/types";
  import GameMapBoard from "../components/GameMapBoard.svelte";
  import HintDock from "../components/HintDock.svelte";
  import RaceCountdown from "../components/RaceCountdown.svelte";
  import RaceStrip from "../components/RaceStrip.svelte";
  import RoundMasthead from "../components/RoundMasthead.svelte";

  let {
    session,
    room,
    relayConnection = "connected",
    busy = false,
    onFollow,
    onBack,
    onHint,
  }: {
    session: SessionSnapshot;
    room?: RoomSnapshot;
    relayConnection?: RelayConnectionState;
    busy?: boolean;
    onFollow: (token: string) => void;
    onBack: () => void;
    onHint: (type: HintType, propertyId?: string) => void;
  } = $props();

  let liveSeconds = $state(0);
  let compassSelecting = $state(false);

  onMount(() => {
    liveSeconds = session.elapsed_seconds;
    const interval = window.setInterval(() => {
      if (session.status === "active") liveSeconds += 1;
    }, 1000);
    return () => window.clearInterval(interval);
  });

  $effect(() => {
    liveSeconds = Math.max(liveSeconds, session.elapsed_seconds);
  });

  function handleKeydown(event: KeyboardEvent): void {
    const target = event.target;
    if (
      target instanceof HTMLInputElement ||
      target instanceof HTMLTextAreaElement ||
      target instanceof HTMLButtonElement
    )
      return;
    if (event.key.toLowerCase() === "b" && session.trail.length > 1 && !busy)
      onBack();
  }

  function toggleCompassSelection(): void {
    compassSelecting = !compassSelecting;
  }

  function useCompass(propertyId: string): void {
    compassSelecting = false;
    onHint("compass", propertyId);
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<main class="game-page" aria-busy={busy}>
  {#if room}<RaceCountdown active={room.state === "countdown"} />{/if}
  {#if room}
    <RaceStrip
      {room}
      currentMoves={session.moves}
      connection={relayConnection}
    />
  {/if}

  <RoundMasthead
    startLabel={session.start.label}
    targetLabel={session.target.label}
    modeLabel={session.mode === "daily"
      ? "Daily connection"
      : room
        ? "Live relay"
        : "Solo route"}
    difficulty={session.difficulty === "easy"
      ? "Easy"
      : session.difficulty === "hard"
        ? "Hard"
        : "Normal"}
    moves={session.moves}
    par={session.shortest_distance}
    seconds={liveSeconds}
    score={session.score}
    canGoBack={session.trail.length > 1}
    {busy}
    {onBack}
  />

  <GameMapBoard
    {session}
    {busy}
    {compassSelecting}
    {onFollow}
    onCompassSelect={useCompass}
  />

  <HintDock
    groups={session.relation_groups}
    used={session.hints_used}
    disabled={busy}
    {compassSelecting}
    {onHint}
    onCompassToggle={toggleCompassSelection}
  />
</main>
