<script lang="ts">
  import AtlasIcon from "../components/AtlasIcon.svelte";

  const glyphs = [
    "origin",
    "place",
    "work",
    "part",
    "nature",
    "influence",
  ] as const;
</script>

<main class="lab-page">
  <header class="lab-header">
    <p class="eyebrow">Internal route · /lab</p>
    <h1>Webwoven field kit</h1>
    <p>
      A living inventory of type, color, relation marks, and interaction states.
      Nothing here bypasses the shared design tokens.
    </p>
  </header>

  <section class="lab-section" aria-labelledby="type-lab">
    <div class="lab-section__index">01</div>
    <div class="lab-section__body">
      <h2 id="type-lab">Typography</h2>
      <div class="type-specimen type-specimen--display">
        <span>Newsreader · Display</span>
        <p>Knowledge has no straight edges.</p>
      </div>
      <div class="type-specimen type-specimen--interface">
        <span>IBM Plex Sans · Interface</span>
        <p>Follow a named relation to continue your route.</p>
      </div>
      <div class="type-specimen type-specimen--technical">
        <span>IBM Plex Mono · Technical</span>
        <p>GRAPH 2026.07 · MOVE 04 · 01:42</p>
      </div>
    </div>
  </section>

  <section class="lab-section" aria-labelledby="color-lab">
    <div class="lab-section__index">02</div>
    <div class="lab-section__body">
      <h2 id="color-lab">Cartographic inks</h2>
      <div class="ink-strips">
        <div class="ink-strip ink-strip--paper"><span>Paper</span></div>
        <div class="ink-strip ink-strip--ink"><span>Ink</span></div>
        <div class="ink-strip ink-strip--signal"><span>Signal</span></div>
        <div class="ink-strip ink-strip--moss"><span>Moss</span></div>
        <div class="ink-strip ink-strip--ochre"><span>Ochre</span></div>
        <div class="ink-strip ink-strip--cartographic">
          <span>Cartographic</span>
        </div>
      </div>
    </div>
  </section>

  <section class="lab-section" aria-labelledby="glyph-lab">
    <div class="lab-section__index">03</div>
    <div class="lab-section__body">
      <h2 id="glyph-lab">Relation marks</h2>
      <div class="glyph-specimens">
        {#each glyphs as glyph}
          <div><AtlasIcon name={glyph} size={30} /><span>{glyph}</span></div>
        {/each}
      </div>
    </div>
  </section>

  <section class="lab-section" aria-labelledby="control-lab">
    <div class="lab-section__index">04</div>
    <div class="lab-section__body">
      <h2 id="control-lab">Controls</h2>
      <div class="control-specimens">
        <button type="button" class="primary-action"
          >Primary bearing <AtlasIcon name="arrow" size={19} /></button
        >
        <button type="button" class="secondary-action">Secondary action</button>
        <button type="button" class="text-action">Text action</button>
        <button type="button" class="secondary-action" disabled
          >Unavailable</button
        >
      </div>
    </div>
  </section>
</main>
