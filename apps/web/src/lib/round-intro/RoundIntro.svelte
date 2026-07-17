<script lang="ts">
  import { onMount } from "svelte";
  import type { SessionSnapshot } from "../api/types";
  import EndpointArtwork from "../components/EndpointArtwork.svelte";
  import { gameModeLabel } from "../domain/game-mode-presentation";
  import { shouldReduceMotion } from "../preferences/preferences";
  import { categoryTheme } from "./assets";
  import RoundIntroCanvas from "./RoundIntroCanvas.svelte";
  import { roundIntroTimeline } from "./timeline";

  let {
    session,
    onComplete,
  }: {
    session: SessionSnapshot;
    onComplete: () => void;
  } = $props();

  const theme = $derived(categoryTheme(session.category));
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
      `--intro-accent: ${theme.accent}`,
      `--category-opacity: ${timeline.category * (1 - categoryExit)}`,
      `--category-shift: ${categoryExit * -48}px`,
      `--endpoint-opacity: ${timeline.endpoints}`,
      `--endpoint-scale: ${1.08 - timeline.zoom_out * 0.44}`,
      `--endpoint-scale-mobile: ${1.02 - timeline.zoom_out * 0.18}`,
      `--endpoint-inset: ${(1 - timeline.zoom_out) * 8}vw`,
      `--endpoint-inset-negative: ${(1 - timeline.zoom_out) * -8}vw`,
      `--endpoint-inset-mobile: ${(1 - timeline.zoom_out) * 3.5}vh`,
      `--endpoint-inset-mobile-negative: ${(1 - timeline.zoom_out) * -3.5}vh`,
      `--intro-opacity: ${1 - timeline.handoff}`,
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
  style={visualStyle}
  aria-label={`Round begins in ${countdown} seconds`}
>
  {#if !reducedMotion && !webglUnavailable}
    <RoundIntroCanvas
      {timeline}
      accent={theme.accent}
      onUnavailable={() => (webglUnavailable = true)}
    />
  {/if}

  <div class="round-intro__registration">
    <strong class="round-intro__mode">{gameModeLabel(session.mode)}</strong>
  </div>

  <div class="round-intro__category">
    <p>Atlas category</p>
    <h1>{theme.label}</h1>
    <span>{session.difficulty} route</span>
  </div>

  <div class="round-intro__endpoints">
    <p class="round-intro__endpoint-category" aria-hidden="true">
      <span>Atlas category</span>
      <strong>{theme.label}</strong>
    </p>
    <article
      class="round-intro__card round-intro__card--start round-intro__card--with-artwork"
    >
      <EndpointArtwork
        entity={session.start}
        endpoint="start"
        className="round-intro__artwork"
        loading="eager"
        fit="contain"
      />
      <span>Start</span>
      <h2>{session.start.label}</h2>
      <p>{session.start.description}</p>
    </article>
    <article
      class="round-intro__card round-intro__card--goal round-intro__card--with-artwork"
    >
      <EndpointArtwork
        entity={session.target}
        endpoint="goal"
        className="round-intro__artwork"
        loading="eager"
        fit="contain"
      />
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
