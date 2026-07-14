<script lang="ts">
  import { onMount } from "svelte";
  import type { SessionSnapshot } from "../api/types";
  import { shouldReduceMotion } from "../preferences/preferences";
  import { categoryArtwork } from "./assets";
  import RoundIntroCanvas from "./RoundIntroCanvas.svelte";
  import { roundIntroTimeline } from "./timeline";

  let {
    session,
    onComplete,
  }: {
    session: SessionSnapshot;
    onComplete: () => void;
  } = $props();

  const artwork = $derived(categoryArtwork(session.category));
  let now = $state(Date.now());
  let webglUnavailable = $state(false);
  let reducedMotion = $state(false);
  let completed = false;
  let timeline = $derived(roundIntroTimeline(session.started_at, now));
  let countdown = $derived(
    Math.max(1, Math.ceil(timeline.remaining_ms / 1000)),
  );
  let categoryExit = $derived(Math.min(1, timeline.endpoints * 4));
  let visualStyle = $derived(
    [
      `--intro-accent: ${artwork.accent}`,
      `--category-opacity: ${timeline.category * (1 - categoryExit)}`,
      `--category-shift: ${categoryExit * -48}px`,
      `--endpoint-opacity: ${timeline.endpoints}`,
      `--endpoint-overlap: ${(1 - timeline.endpoints) * 38}%`,
      `--endpoint-overlap-negative: ${(1 - timeline.endpoints) * -38}%`,
      `--endpoint-turn: ${(1 - timeline.endpoints) * 2}deg`,
      `--endpoint-turn-negative: ${(1 - timeline.endpoints) * -2}deg`,
      `--thread-scale: ${timeline.endpoints}`,
      `--launch-x: ${timeline.launch * 38}vw`,
      `--launch-y: ${timeline.launch * 25}vh`,
      `--launch-scale: ${1 + timeline.launch * 3.5}`,
      `--launch-fade: ${1 - timeline.launch}`,
    ].join("; "),
  );

  onMount(() => {
    reducedMotion = shouldReduceMotion();
    let frame = 0;
    const tick = (): void => {
      now = Date.now();
      if (timeline.phase === "complete") {
        completeOnce();
        return;
      }
      frame = requestAnimationFrame(tick);
    };
    tick();
    const recover = (): void => {
      now = Date.now();
      if (timeline.phase === "complete") completeOnce();
    };
    document.addEventListener("visibilitychange", recover);
    return () => {
      cancelAnimationFrame(frame);
      document.removeEventListener("visibilitychange", recover);
    };
  });

  function completeOnce(): void {
    if (completed) return;
    completed = true;
    onComplete();
  }
</script>

<section
  class="round-intro"
  class:round-intro--static={reducedMotion || webglUnavailable}
  class:round-intro--launch={timeline.phase === "launch"}
  style={visualStyle}
  aria-label={`Round begins in ${countdown} seconds`}
>
  {#if !reducedMotion && !webglUnavailable}
    <RoundIntroCanvas
      {timeline}
      artwork={artwork.image}
      accent={artwork.accent}
      start={session.start}
      target={session.target}
      onUnavailable={() => (webglUnavailable = true)}
    />
  {/if}

  <div class="round-intro__registration" aria-hidden="true">
    <span>WW / {session.id.slice(0, 6).toUpperCase()}</span>
    <span>{String(countdown).padStart(2, "0")} SEC</span>
  </div>

  <div class="round-intro__category">
    <p>Atlas category</p>
    <h1>{artwork.label}</h1>
    <span>{session.difficulty} route</span>
  </div>

  <div class="round-intro__endpoints">
    <article class="round-intro__card round-intro__card--start">
      {#if session.start.image_path}
        <img src={session.start.image_path} alt="" />
      {/if}
      <span>Start</span>
      <h2>{session.start.label}</h2>
      <p>{session.start.description}</p>
    </article>
    <div class="round-intro__thread" aria-hidden="true"><i></i></div>
    <article class="round-intro__card round-intro__card--goal">
      {#if session.target.image_path}
        <img src={session.target.image_path} alt="" />
      {/if}
      <span>Goal</span>
      <h2>{session.target.label}</h2>
      <p>{session.target.description}</p>
    </article>
  </div>

  {#if reducedMotion || webglUnavailable}
    <p class="round-intro__fallback" role="timer" aria-live="polite">
      Route opens in {countdown}
    </p>
  {/if}
</section>
