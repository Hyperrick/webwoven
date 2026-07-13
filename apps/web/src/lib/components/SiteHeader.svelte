<script lang="ts">
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    compact = false,
    onHome,
    onSources,
    onSettings,
  }: {
    compact?: boolean;
    onHome: () => void;
    onSources: () => void;
    onSettings: () => void;
  } = $props();
</script>

<header class:site-header--compact={compact} class="site-header">
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
