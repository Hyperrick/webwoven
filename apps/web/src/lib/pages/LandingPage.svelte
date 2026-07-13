<script lang="ts">
  import AtlasIcon from "../components/AtlasIcon.svelte";
  import SiteFooter from "../components/SiteFooter.svelte";

  let {
    onSolo,
    onDaily,
    onRelay,
  }: {
    onSolo: () => void;
    onDaily: () => void;
    onRelay: () => void;
  } = $props();

  const route = [
    "Hokusai",
    "The Great Wave",
    "British Museum",
    "London",
    "United Kingdom",
  ];
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
      <div class="hero__actions">
        <button class="primary-action" type="button" onclick={onSolo}>
          Begin a route <AtlasIcon name="arrow" size={20} />
        </button>
        <button class="text-action" type="button" onclick={onDaily}
          >Play today’s connection</button
        >
      </div>
    </div>

    <div class="hero-route" aria-label="Example knowledge route">
      <div class="hero-route__stamp">
        <span>Route no.</span><strong>0042</strong>
      </div>
      <ol>
        {#each route as entity, index}
          <li>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{entity}</strong>
            {#if index < route.length - 1}<i aria-hidden="true"></i>{/if}
          </li>
        {/each}
      </ol>
      <p>Four moves · Culture → Places</p>
    </div>
  </section>

  <section class="mode-ledger" aria-labelledby="modes-title">
    <header class="section-intro">
      <p class="eyebrow">Three ways in</p>
      <h2 id="modes-title">Choose your expedition</h2>
      <p>
        Every route begins with the same question: what could possibly connect
        these two?
      </p>
    </header>

    <div class="mode-ledger__rows">
      <button class="mode-row" type="button" onclick={onSolo}>
        <span class="mode-row__number">01</span>
        <span class="mode-row__title"
          ><strong>Solo route</strong><small>Explore at your own pace</small
          ></span
        >
        <span class="mode-row__copy"
          >Reach the destination with as few moves as possible. Hints are there
          when the map goes quiet.</span
        >
        <AtlasIcon name="arrow" size={23} />
      </button>
      <button class="mode-row" type="button" onclick={onDaily}>
        <span class="mode-row__number">02</span>
        <span class="mode-row__title"
          ><strong>Daily connection</strong><small
            >One shared route each day</small
          ></span
        >
        <span class="mode-row__copy"
          >Compare paths without spoilers, then see how your score and time meet
          the field.</span
        >
        <AtlasIcon name="arrow" size={23} />
      </button>
      <button class="mode-row" type="button" onclick={onRelay}>
        <span class="mode-row__number">03</span>
        <span class="mode-row__title"
          ><strong>Live relay</strong><small>Two to four explorers</small></span
        >
        <span class="mode-row__copy"
          >Race the same map together. See progress, never another player’s
          current answer.</span
        >
        <AtlasIcon name="arrow" size={23} />
      </button>
    </div>
  </section>

  <section class="manifesto" aria-labelledby="manifesto-title">
    <div class="manifesto__mark" aria-hidden="true">
      <span></span><span></span><span></span>
    </div>
    <div>
      <p class="eyebrow">Codex-native development</p>
      <h2 id="manifesto-title">
        Everyone with an idea can become a game developer.
      </h2>
      <p>
        Webwoven is both a game and a Build Week field journal: a transparent
        record of an idea becoming a careful, playable system with Codex as a
        native development collaborator.
      </p>
    </div>
    <dl>
      <div>
        <dt>Knowledge</dt>
        <dd>Open and attributed</dd>
      </div>
      <div>
        <dt>Routes</dt>
        <dd>Curated before release</dd>
      </div>
      <div>
        <dt>AI at runtime</dt>
        <dd>None</dd>
      </div>
    </dl>
  </section>

  <SiteFooter />
</main>
