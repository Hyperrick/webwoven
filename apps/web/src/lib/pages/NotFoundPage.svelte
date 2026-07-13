<script lang="ts">
  let { onHome }: { onHome: () => void } = $props();
</script>

<main class="not-found">
  <p class="not-found__code">404</p>
  <p class="eyebrow">Uncharted margin</p>
  <h1>This route leaves the known atlas.</h1>
  <p>The page may have moved, or the connection has not been drawn yet.</p>
  <button class="primary-action" type="button" onclick={onHome}
    >Return to Webwoven</button
  >
</main>
