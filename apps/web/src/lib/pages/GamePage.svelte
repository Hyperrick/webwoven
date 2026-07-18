<script lang="ts">
  import { onMount } from "svelte";
  import type { RelayConnectionState } from "../api/room-event-stream";
  import type { HintType, RoomSnapshot, SessionSnapshot } from "../api/types";
  import GameMapBoard from "../components/GameMapBoard.svelte";
  import HintDock from "../components/HintDock.svelte";
  import RaceStrip from "../components/RaceStrip.svelte";
  import RoundMasthead from "../components/RoundMasthead.svelte";
  import { activeBackDestination } from "../domain/back-navigation";
  import { gameModeLabel } from "../domain/game-mode-presentation";
  import { relayGraceRemainingSeconds } from "../domain/relay-grace";
  import RoundIntro from "../round-intro/RoundIntro.svelte";

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
    onHint: (type: HintType, propertyId?: string, entityQid?: string) => void;
  } = $props();

  let now = $state(Date.now());
  let completedIntroId = $state<string>();
  let compassSelecting = $state(false);
  let backDestination = $derived(activeBackDestination(session));
  let canGoBack = $derived(Boolean(backDestination));
  let introActive = $derived(
    completedIntroId !== session.id && Date.parse(session.started_at) > now,
  );
  let graceSeconds = $derived(
    room ? relayGraceRemainingSeconds(room, now) : null,
  );
  let relayEnded = $derived(
    Boolean(
      room &&
      (room.state === "finished" ||
        room.state === "closed" ||
        (room.state === "grace_period" && graceSeconds === 0)),
    ),
  );
  let locked = $derived(busy || introActive || relayEnded);
  let liveSeconds = $derived.by(() => {
    const started = Date.parse(session.started_at);
    const elapsed = Number.isFinite(started)
      ? Math.max(0, Math.floor((now - started) / 1_000))
      : 0;
    return Math.max(session.elapsed_seconds, elapsed);
  });

  onMount(() => {
    const interval = window.setInterval(() => {
      now = Date.now();
    }, 250);
    return () => window.clearInterval(interval);
  });

  function handleKeydown(event: KeyboardEvent): void {
    const target = event.target;
    if (
      target instanceof HTMLInputElement ||
      target instanceof HTMLTextAreaElement ||
      target instanceof HTMLButtonElement
    )
      return;
    if (event.key.toLowerCase() === "b" && canGoBack && !locked) onBack();
  }

  function toggleCompassSelection(): void {
    compassSelecting = !compassSelecting;
  }

  function useCompass(propertyId: string, entityQid: string): void {
    compassSelecting = false;
    onHint("compass", propertyId, entityQid);
  }

  $effect(() => {
    if (session.relation_groups.length === 0) compassSelecting = false;
  });
</script>

<svelte:window onkeydown={handleKeydown} />

<main class="game-page" aria-busy={locked}>
  <div class="game-page__play" inert={introActive} aria-hidden={introActive}>
    {#if room}
      <RaceStrip
        {room}
        currentMoves={session.moves}
        connection={relayConnection}
        {now}
      />
    {/if}

    <RoundMasthead
      startLabel={session.start.label}
      targetLabel={session.target.label}
      modeLabel={gameModeLabel(session.mode)}
      difficulty={session.difficulty === "easy"
        ? "Easy"
        : session.difficulty === "hard"
          ? "Hard"
          : "Normal"}
      moves={session.moves}
      seconds={liveSeconds}
      score={session.score}
      {canGoBack}
      busy={locked}
      {onBack}
    />

    <GameMapBoard
      {session}
      busy={locked}
      active={!introActive}
      {canGoBack}
      {compassSelecting}
      {onFollow}
      {onBack}
      backDestinationLabel={backDestination?.label}
      onCompassSelect={useCompass}
    >
      {#snippet railFooter()}
        <HintDock
          groups={session.relation_groups}
          used={session.hints_used}
          disabled={locked}
          {compassSelecting}
          {onHint}
          onCompassToggle={toggleCompassSelection}
        />
      {/snippet}
    </GameMapBoard>
  </div>

  {#if introActive}
    <RoundIntro {session} onComplete={() => (completedIntroId = session.id)} />
  {/if}
</main>
