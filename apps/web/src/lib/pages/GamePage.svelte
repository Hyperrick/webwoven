<script lang="ts">
  import { onMount } from "svelte";
  import type { RelayConnectionState } from "../api/room-event-stream";
  import type { HintType, RoomSnapshot, SessionSnapshot } from "../api/types";
  import AtlasIcon from "../components/AtlasIcon.svelte";
  import EntityStage from "../components/EntityStage.svelte";
  import GameMetrics from "../components/GameMetrics.svelte";
  import HintDock from "../components/HintDock.svelte";
  import RaceCountdown from "../components/RaceCountdown.svelte";
  import RaceStrip from "../components/RaceStrip.svelte";
  import RelationGroups from "../components/RelationGroups.svelte";
  import RouteRibbon from "../components/RouteRibbon.svelte";

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

  <div class="game-page__utility">
    <p>
      <span
        >{session.mode === "daily"
          ? "Daily connection"
          : room
            ? "Live relay"
            : "Solo route"}</span
      > · Normal
    </p>
    <button
      class="back-action"
      type="button"
      disabled={busy || session.trail.length < 2}
      onclick={onBack}
    >
      <AtlasIcon name="back" size={19} /> In-game Back <kbd>B</kbd>
    </button>
  </div>

  <RouteRibbon trail={session.trail} target={session.target} />

  <section class="game-spread">
    <aside class="destination-brief">
      <p class="eyebrow">Destination</p>
      <span class="destination-brief__index">{session.target.qid}</span>
      <h2>{session.target.label}</h2>
      <p>{session.target.description}</p>
      <div class="destination-brief__rule"></div>
      <p class="destination-brief__par">
        Optimal known route <strong
          >{session.shortest_distance === null
            ? "Pending"
            : `${session.shortest_distance} moves`}</strong
        >
      </p>
    </aside>

    <div class="game-spread__main">
      <GameMetrics
        moves={session.moves}
        par={session.shortest_distance}
        seconds={liveSeconds}
        score={session.score}
      />
      <EntityStage entity={session.current} />
      {#if session.last_connection}
        <p class="connection-note" role="status">
          <span>Last connection</span>{session.last_connection}
        </p>
      {/if}
      <RelationGroups
        groups={session.relation_groups}
        disabled={busy}
        {onFollow}
      />
    </div>
  </section>

  <HintDock
    groups={session.relation_groups}
    used={session.hints_used}
    disabled={busy}
    {onHint}
  />
</main>
