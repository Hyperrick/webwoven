<script lang="ts">
  import type { DailyLeaderboard, SessionSnapshot } from "../api/types";
  import AtlasIcon from "../components/AtlasIcon.svelte";
  import { routeRecap } from "../domain/route-recap";

  let {
    session,
    leaderboard,
    leaderboardStatus,
    leaderboardError,
    onLeaderboardRetry,
    onAgain,
    onDaily,
    onHome,
  }: {
    session: SessionSnapshot;
    leaderboard: DailyLeaderboard;
    leaderboardStatus: "idle" | "loading" | "ready" | "error";
    leaderboardError: string;
    onLeaderboardRetry: () => void;
    onAgain: () => void;
    onDaily: () => void;
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
  const currentIsVisible = $derived(
    leaderboard.entries.some((entry) => entry.is_current_guest),
  );
</script>

<main class="results-page">
  <section class="result-hero" aria-labelledby="result-title">
    <div class="result-hero__seal">
      <AtlasIcon name="check" size={34} /><span>Route complete</span>
    </div>
    <div class="result-hero__copy">
      <p class="eyebrow">The atlas closes here</p>
      <h1 id="result-title">You found<br /><em>{session.target.label}.</em></h1>
      <p>
        {session.start.label} was {session.moves} moves away—at least by the route
        you chose.
      </p>
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
        <li class:route-reveal__item--revisited={item.revisited}>
          <span>{String(index + 1).padStart(2, "0")}</span>
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
        <p>Deterministic recap from the route recorded above.</p>
      </div>
    </div>
    {#if session.mode === "daily"}
      <div class="leaderboard">
        <header>
          <h2>Today’s field</h2>
          <span>UTC</span>
        </header>
        {#if leaderboardStatus === "loading" || leaderboardStatus === "idle"}
          <p class="leaderboard__status" role="status">
            Reading today’s field…
          </p>
        {:else if leaderboardStatus === "error"}
          <div class="leaderboard__status" role="alert">
            <p>
              {leaderboardError || "Today’s field is temporarily unavailable."}
            </p>
            <button
              class="secondary-action"
              type="button"
              onclick={onLeaderboardRetry}
            >
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
                  >{leaderboard.current_guest_entry.display_name}<em>You</em
                  ></strong
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
    {:else}
      <div class="next-route">
        <p class="eyebrow">Keep mapping</p>
        <h2>A new route is waiting.</h2>
        <p>The same two points can hold more than one good answer.</p>
        <button class="primary-action" type="button" onclick={onAgain}
          >Try another route <AtlasIcon name="arrow" size={20} /></button
        >
        <button class="text-action" type="button" onclick={onDaily}
          >Play today’s connection</button
        >
      </div>
    {/if}
  </section>

  <button class="result-home" type="button" onclick={onHome}
    >Return to frontispiece</button
  >
</main>
