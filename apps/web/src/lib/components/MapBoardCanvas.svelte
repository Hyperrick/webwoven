<script lang="ts">
  import { onMount } from "svelte";
  import type { MapBoard } from "../domain/map-board";
  import "../../styles/map-board.css";
  import type { AtlasMapRenderer } from "./map-board-renderer";

  let {
    board,
    class: className = "",
  }: {
    board: MapBoard;
    class?: string;
  } = $props();

  let host: HTMLDivElement;
  let renderer = $state<AtlasMapRenderer | null>(null);
  let reducedMotion = $state(false);
  let renderState = $state<"loading" | "ready" | "fallback">("loading");
  let nodesById = $derived(new Map(board.nodes.map((node) => [node.id, node])));

  onMount(() => {
    let cancelled = false;
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const setMotionPreference = (): void => {
      reducedMotion =
        motionQuery.matches ||
        document.documentElement.dataset.motion === "reduced";
    };
    setMotionPreference();
    motionQuery.addEventListener("change", setMotionPreference);
    const motionObserver = new MutationObserver(setMotionPreference);
    motionObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-motion"],
    });

    let instance: AtlasMapRenderer | null = null;
    let observer: ResizeObserver | null = null;
    const startRenderer = async (): Promise<void> => {
      try {
        const { AtlasMapRenderer } = await import("./map-board-renderer");
        if (cancelled) return;
        instance = new AtlasMapRenderer(host, () => {
          renderState = "fallback";
        });
        renderer = instance;
        observer = new ResizeObserver(([entry]) => {
          if (!entry) return;
          instance?.resize(entry.contentRect.width, entry.contentRect.height);
        });
        observer.observe(host);
        const bounds = host.getBoundingClientRect();
        instance.resize(bounds.width, bounds.height);
        renderState = "ready";
      } catch {
        instance?.dispose();
        renderer = null;
        if (!cancelled) renderState = "fallback";
      }
    };
    void startRenderer();

    return () => {
      cancelled = true;
      motionQuery.removeEventListener("change", setMotionPreference);
      motionObserver.disconnect();
      observer?.disconnect();
      instance?.dispose();
      renderer = null;
    };
  });

  $effect(() => {
    renderer?.setBoard(board.nodes, board.links, reducedMotion);
  });
</script>

<div
  class={`map-board-renderer ${className}`}
  data-render-state={renderState}
  aria-hidden="true"
  bind:this={host}
>
  {#if renderState === "fallback"}
    <svg
      class="map-board-fallback"
      viewBox="0 0 1000 600"
      preserveAspectRatio="none"
    >
      {#each board.links as link (link.id)}
        {@const source = nodesById.get(link.source_node_id)}
        {@const target = nodesById.get(link.target_node_id)}
        {#if source && target}
          <line
            class:map-board-fallback__link--trail={link.kind === "trail"}
            class="map-board-fallback__link"
            x1={source.position.x * 1000}
            y1={source.position.y * 600}
            x2={target.position.x * 1000}
            y2={target.position.y * 600}
          />
        {/if}
      {/each}
      {#each board.nodes as node (node.id)}
        <circle
          class:map-board-fallback__node--trail={node.roles.includes("trail")}
          class:map-board-fallback__node--choice={node.roles.includes("choice")}
          class:map-board-fallback__node--goal={node.roles.includes("goal")}
          class:map-board-fallback__node--current={node.roles.includes(
            "current",
          )}
          class="map-board-fallback__node"
          cx={node.position.x * 1000}
          cy={node.position.y * 600}
          r={node.roles.includes("current") ? 18 : 13}
        />
      {/each}
    </svg>
  {/if}
</div>
