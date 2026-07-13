<script lang="ts">
  import AtlasIcon from "./AtlasIcon.svelte";

  let { message }: { message: string } = $props();
</script>

{#if message}
  <div class="status-toast" role="status">
    <AtlasIcon name="check" size={18} />
    <span>{message}</span>
  </div>
{/if}
