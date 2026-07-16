<script lang="ts">
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    compact = false,
    leaderboardOpen,
    pageInert,
    onHome,
    onLeaderboard,
    onSources,
    onSettings,
  }: {
    compact?: boolean;
    leaderboardOpen: boolean;
    pageInert: boolean;
    onHome: () => void;
    onLeaderboard: () => void;
    onSources: () => void;
    onSettings: () => void;
  } = $props();
</script>

<header
  class:site-header--compact={compact}
  class="site-header"
  inert={pageInert}
>
  <button
    class="wordmark"
    type="button"
    onclick={onHome}
    aria-label="Webwoven home"
  >
    <span class="wordmark__weave" aria-hidden="true"><i></i><i></i><i></i></span
    >
    <span>Webwoven</span>
  </button>

  <div class="site-header__actions">
    <button
      class="icon-button icon-button--label"
      type="button"
      onclick={onLeaderboard}
      aria-label="Open Daily leaderboard"
      aria-haspopup="dialog"
      aria-controls="daily-leaderboard-drawer"
      aria-expanded={leaderboardOpen}
    >
      <AtlasIcon name="leaderboard" size={18} />
      <span>Daily leaderboard</span>
    </button>
    <button
      class="icon-button icon-button--label"
      type="button"
      onclick={onSources}
      aria-label="Open sources"
    >
      <AtlasIcon name="sources" size={18} />
      <span>Sources</span>
    </button>
    <button
      class="icon-button"
      type="button"
      onclick={onSettings}
      aria-label="Open settings"
    >
      <AtlasIcon name="settings" size={19} />
    </button>
  </div>
</header>
