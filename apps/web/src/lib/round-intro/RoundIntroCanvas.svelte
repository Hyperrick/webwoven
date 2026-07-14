<script lang="ts">
  import { onMount } from "svelte";
  import type { EntitySummary } from "../api/types";
  import type { RoundIntroTimeline } from "./timeline";
  import type { RoundIntroScene } from "./scene";

  let {
    timeline,
    artwork,
    accent,
    start,
    target,
    onUnavailable,
  }: {
    timeline: RoundIntroTimeline;
    artwork: string;
    accent: string;
    start: EntitySummary;
    target: EntitySummary;
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
          artwork,
          accent,
          startImage: start.image_path,
          targetImage: target.image_path,
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
