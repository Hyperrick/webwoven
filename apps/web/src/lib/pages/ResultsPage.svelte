<script lang="ts">
  import type { LeaderboardEntry, SessionSnapshot } from "../api/types";
  import AtlasIcon from "../components/AtlasIcon.svelte";

  let {
    session,
    leaderboard,
    onAgain,
    onDaily,
    onHome,
    onShare,
  }: {
    session: SessionSnapshot;
    leaderboard: LeaderboardEntry[];
    onAgain: () => void;
    onDaily: () => void;
    onHome: () => void;
    onShare: () => void;
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
      <button class="secondary-action" type="button" onclick={onShare}
        >Copy spoiler-free result</button
      >
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
      <p class="eyebrow">Cartographer’s note</p>
      <blockquote>
        “You crossed from an artist into geography through a work and the museum
        that holds it. That is a fine piece of mapmaking.”
      </blockquote>
      <p>Generated from the reviewed facts on this route.</p>
    </div>
    {#if session.mode === "daily"}
      <div class="leaderboard">
        <header>
          <h2>Today’s field</h2>
          <span>UTC</span>
        </header>
        <ol>
          {#each leaderboard as entry (entry.rank)}
            <li class:leaderboard__you={entry.is_current_guest}>
              <span>{entry.rank}</span><strong>{entry.display_name}</strong
              ><small>{entry.moves} moves · {entry.elapsed_seconds}s</small><b
                >{entry.score}</b
              >
            </li>
          {/each}
        </ol>
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
