<script lang="ts">
  import { onMount } from "svelte";
  import type { RoundIntroTimeline } from "./timeline";
  import type { RoundIntroScene } from "./scene";

  let {
    timeline,
    accent,
    onUnavailable,
  }: {
    timeline: RoundIntroTimeline;
    accent: string;
    onUnavailable: () => void;
  } = $props();

  let host: HTMLDivElement;
  let scene = $state<RoundIntroScene>();

  onMount(() => {
    let cancelled = false;
    let instance: RoundIntroScene | undefined;
    void import("./scene")
      .then(({ RoundIntroScene: Scene }) => {
        if (cancelled) return;
        instance = new Scene(host, {
          accent,
          onUnavailable,
        });
        scene = instance;
      })
      .catch(onUnavailable);
    return () => {
      cancelled = true;
      instance?.dispose();
      scene = undefined;
    };
  });

  $effect(() => {
    scene?.update(timeline);
  });
</script>

<div class="round-intro__canvas" aria-hidden="true" bind:this={host}></div>
