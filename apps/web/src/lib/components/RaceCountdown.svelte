<script lang="ts">
  import { onMount } from "svelte";

  let { active }: { active: boolean } = $props();
  let count = $state(3);
  let visible = $state(false);

  onMount(() => {
    visible = active;
    if (!active) return;
    const interval = window.setInterval(() => {
      count -= 1;
      if (count <= 0) {
        visible = false;
        window.clearInterval(interval);
      }
    }, 1000);
    return () => window.clearInterval(interval);
  });
</script>

{#if visible}
  <div class="countdown" role="status" aria-live="assertive">
    <p>Same start. Same destination.</p>
    <strong>{count}</strong>
    <span>Map opens together</span>
  </div>
{/if}
