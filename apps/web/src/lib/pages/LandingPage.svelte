<script lang="ts">
  import PlayModeChooser from "../components/PlayModeChooser.svelte";
  import SiteFooter from "../components/SiteFooter.svelte";
  import { createLandingRoutePreview } from "../domain/landing-route-preview";

  let {
    onSolo,
    onDaily,
    onRelay,
  }: {
    onSolo: () => void;
    onDaily: () => void;
    onRelay: () => void;
  } = $props();

  const route = createLandingRoutePreview();
</script>

<main class="landing-page">
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero__copy">
      <p class="eyebrow">A game of open knowledge</p>
      <h1 id="hero-title">
        The shortest route is rarely a <em>straight line.</em>
      </h1>
      <p class="hero__lede">
        Move through real, named connections. Find an elegant path between two
        things that seem worlds apart.
      </p>
      <PlayModeChooser {onSolo} {onDaily} {onRelay} />
    </div>

    <div class="hero-route" aria-label="Example knowledge route">
      <div class="hero-route__stamp">
        <span>Route no.</span><strong>{route.number}</strong>
      </div>
      <ol>
        {#each route.steps as step, index}
          <li class:hero-route__step--hidden={step.hidden}>
            <span>{step.number}</span>
            <strong aria-label={step.hidden ? "Connection hidden" : undefined}
              >{step.label}</strong
            >
            {#if index < route.steps.length - 1}<i aria-hidden="true"></i>{/if}
          </li>
        {/each}
      </ol>
      <p>{route.moves} moves · {route.categoryPath}</p>
    </div>
  </section>

  <SiteFooter />
</main>
