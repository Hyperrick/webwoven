<script lang="ts">
  import type {
    DailyLeaderboard,
    RoomSnapshot,
    SessionSnapshot,
  } from "../api/types";
  import AtlasIcon from "../components/AtlasIcon.svelte";
  import DailyLeaderboardTable from "../components/DailyLeaderboard.svelte";
  import EndpointArtwork from "../components/EndpointArtwork.svelte";
  import RelayResultActions from "../components/RelayResultActions.svelte";
  import { gameModeLabel } from "../domain/game-mode-presentation";
  import { routeRecap } from "../domain/route-recap";
  import { trailEntityAt } from "../domain/trail-entities";

  let {
    session,
    leaderboard,
    leaderboardStatus,
    leaderboardError,
    room,
    relayBusy = false,
    onLeaderboardRetry,
    onSolo,
    onDaily,
    onRelay,
    onRelayVote,
    onRelayRefresh,
    onHome,
  }: {
    session: SessionSnapshot;
    leaderboard: DailyLeaderboard;
    leaderboardStatus: "idle" | "loading" | "ready" | "error";
    leaderboardError: string;
    room?: RoomSnapshot;
    relayBusy?: boolean;
    onLeaderboardRetry: () => void;
    onSolo: () => void;
    onDaily: () => void;
    onRelay: () => void;
    onRelayVote: (accept: boolean) => void;
    onRelayRefresh: () => void;
    onHome: () => void;
  } = $props();

  const time = $derived(
    `${Math.floor(session.elapsed_seconds / 60)}:${String(session.elapsed_seconds % 60).padStart(2, "0")}`,
  );
  const efficiency = $derived(
    session.shortest_distance === null
      ? null
      : Math.round(
          (session.shortest_distance /
            Math.max(session.moves, session.shortest_distance)) *
            100,
        ),
  );
  const recap = $derived(routeRecap(session));
  const modeLabel = $derived(
    session.mode === "relay"
      ? "Multiplayer round"
      : gameModeLabel(session.mode),
  );
  const resultSeal = $derived(
    session.mode === "daily"
      ? "Daily complete"
      : session.mode === "relay"
        ? session.status === "expired"
          ? "Time expired"
          : "Round complete"
        : "Solo complete",
  );
  const resultSummary = $derived(
    session.mode === "daily"
      ? `Your route through today’s shared connection took ${session.moves} moves. See how it compares with today’s field below.`
      : session.mode === "relay"
        ? session.status === "expired"
          ? `The 30-second final chance ended after ${session.moves} moves. Your route is saved, and the lobby can still choose another round.`
          : `You reached the shared destination in ${session.moves} moves. Stay with the lobby to choose what happens next.`
        : `${session.start.label} was ${session.moves} moves away—at least by the route you chose.`,
  );
</script>

<main class="results-page">
  <section class="result-hero" aria-labelledby="result-title">
    <div class="result-hero__seal">
      <AtlasIcon name="check" size={34} /><span>{resultSeal}</span>
    </div>
    <div class="result-hero__copy">
      <p class="eyebrow">{modeLabel} complete</p>
      <h1 id="result-title">
        {#if session.mode === "relay" && session.status === "expired"}
          Time ran out<br /><em>before {session.target.label}.</em>
        {:else}
          You found<br /><em>{session.target.label}.</em>
        {/if}
      </h1>
      <p>{resultSummary}</p>
    </div>
    <dl class="result-score">
      <div class="result-score__total">
        <dt>Final score</dt>
        <dd>{session.score ?? "—"}</dd>
      </div>
      <div>
        <dt>Moves</dt>
        <dd>{session.moves}</dd>
      </div>
      <div>
        <dt>Time</dt>
        <dd>{time}</dd>
      </div>
      <div>
        <dt>Efficiency</dt>
        <dd>{efficiency === null ? "—" : `${efficiency}%`}</dd>
      </div>
    </dl>
  </section>

  <section class="route-reveal" aria-labelledby="reveal-title">
    <header>
      <div>
        <p class="eyebrow">Route reveal</p>
        <h2 id="reveal-title">The path you wove</h2>
      </div>
    </header>
    <ol>
      {#each session.trail as item, index (`${index}:${item.qid}`)}
        {@const routeEntity = trailEntityAt(session, index)}
        <li
          class:route-reveal__item--revisited={item.revisited}
          class:route-reveal__item--with-artwork={Boolean(routeEntity)}
          data-route-endpoint={index === 0
            ? "start"
            : item.qid === session.target.qid
              ? "goal"
              : undefined}
        >
          {#if routeEntity}
            <EndpointArtwork
              entity={routeEntity}
              endpoint={index === 0
                ? "start"
                : item.qid === session.target.qid
                  ? "goal"
                  : "node"}
              className="route-reveal__artwork"
              fit="contain"
              loading="eager"
            />
          {/if}
          <span class="route-reveal__number"
            >{String(index + 1).padStart(2, "0")}</span
          >
          <div>
            <strong>{item.label}</strong>{#if item.relation}<small
                >{item.relation}</small
              >{/if}
          </div>
        </li>
      {/each}
    </ol>
  </section>

  <section class="result-bottom">
    <div class="cartographer-recap">
      <img
        class="cartographer-recap__portrait"
        src="/illustrations/cartographer.webp"
        alt="Illustration of Webwoven’s fictional Cartographer studying a map laid flat on a field table."
        width="1086"
        height="1448"
        loading="lazy"
        decoding="async"
      />
      <div class="cartographer-recap__copy">
        <p class="eyebrow">Cartographer’s note</p>
        <blockquote>“{recap}”</blockquote>
      </div>
    </div>
    {#if session.mode === "daily"}
      <DailyLeaderboardTable
        {leaderboard}
        status={leaderboardStatus}
        error={leaderboardError}
        onRetry={onLeaderboardRetry}
      />
    {:else if session.mode === "solo"}
      <div class="next-route">
        <p class="eyebrow">Solo route</p>
        <h2>Another route is waiting.</h2>
        <p>Choose a difficulty and map a fresh path at your own pace.</p>
        <div class="next-route__actions">
          <button class="primary-action" type="button" onclick={onSolo}
            >Try another route · Solo <AtlasIcon
              name="arrow"
              size={20}
            /></button
          >
          <button class="text-action" type="button" onclick={onDaily}
            >Play today’s connection</button
          >
        </div>
      </div>
    {:else}
      <RelayResultActions
        {room}
        busy={relayBusy}
        onVote={onRelayVote}
        onRefresh={onRelayRefresh}
        onLobby={onRelay}
        {onSolo}
      />
    {/if}
  </section>

  <button class="result-home" type="button" onclick={onHome}
    >Return to frontispiece</button
  >
</main>
