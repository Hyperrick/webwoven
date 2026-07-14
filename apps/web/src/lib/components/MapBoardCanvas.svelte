<script lang="ts">
  import { onMount } from "svelte";
  import type {
    MapBoard,
    MapBoardLink,
    MapBoardNode,
  } from "../domain/map-board";
  import {
    visibleMapCameraRect,
    type MapCameraView,
  } from "../map-camera/map-camera-view";
  import { shouldReduceMotion } from "../preferences/preferences";
  import "../../styles/map-board.css";
  import type { AtlasMapRenderer } from "./map-board-renderer";
  import {
    mapNodeTokenPresentation,
    mapNodeTokenState,
  } from "./map-node-presentation";

  let {
    board,
    view,
    class: className = "",
  }: {
    board: MapBoard;
    view: MapCameraView;
    class?: string;
  } = $props();

  let host: HTMLDivElement;
  let renderer = $state<AtlasMapRenderer | null>(null);
  let reducedMotion = $state(false);
  let renderState = $state<"loading" | "ready" | "fallback">("loading");
  let nodesById = $derived(new Map(board.nodes.map((node) => [node.id, node])));
  let visibleRect = $derived(visibleMapCameraRect(view));
  let fallbackViewBox = $derived(
    `${visibleRect.x} ${visibleRect.y} ${visibleRect.width} ${visibleRect.height}`,
  );

  function isDiscardedLink(link: MapBoardLink, target: MapBoardNode): boolean {
    return (
      link.kind === "discarded" || mapNodeTokenState(target) === "discarded"
    );
  }

  onMount(() => {
    let cancelled = false;
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const setMotionPreference = (): void => {
      reducedMotion = shouldReduceMotion(undefined, motionQuery.matches);
    };
    setMotionPreference();
    motionQuery.addEventListener("change", setMotionPreference);
    const motionObserver = new MutationObserver(setMotionPreference);
    motionObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-motion"],
    });

    let instance: AtlasMapRenderer | null = null;
    const startRenderer = async (): Promise<void> => {
      try {
        const { AtlasMapRenderer } = await import("./map-board-renderer");
        if (cancelled) return;
        instance = new AtlasMapRenderer(host, () => {
          renderState = "fallback";
        });
        renderer = instance;
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
      instance?.dispose();
      renderer = null;
    };
  });

  $effect(() => {
    const camera: MapCameraView = {
      x: view.x,
      y: view.y,
      zoom: view.zoom,
      world_width: view.world_width,
      world_height: view.world_height,
      viewport_width: view.viewport_width,
      viewport_height: view.viewport_height,
    };
    renderer?.setBoard(
      board.nodes,
      board.links,
      camera.world_width,
      camera.world_height,
      reducedMotion,
    );
    renderer?.setCameraView(camera);
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
      viewBox={fallbackViewBox}
      preserveAspectRatio="none"
    >
      {#each board.links as link (link.id)}
        {@const source = nodesById.get(link.source_node_id)}
        {@const target = nodesById.get(link.target_node_id)}
        {#if source && target}
          <line
            class:map-board-fallback__link--trail={link.kind === "trail"}
            class:map-board-fallback__link--discarded={isDiscardedLink(
              link,
              target,
            )}
            class="map-board-fallback__link"
            x1={source.position.x * view.world_width}
            y1={source.position.y * view.world_height}
            x2={target.position.x * view.world_width}
            y2={target.position.y * view.world_height}
          />
        {/if}
      {/each}
      {#each board.nodes as node (node.id)}
        {@const token = mapNodeTokenPresentation(node)}
        {#if token}
          {@const radius = token.radius}
          {@const cx = node.position.x * view.world_width}
          {@const cy = node.position.y * view.world_height}
          <g
            class:map-board-fallback__marker--discarded={token.state ===
              "discarded"}
            class="map-board-fallback__marker"
          >
            <ellipse
              class="map-board-fallback__node-shadow"
              cx={cx + radius * 0.34}
              cy={cy + radius * 0.52}
              rx={radius * 1.2}
              ry={radius * 0.52}
            />
            <circle
              class="map-board-fallback__node-extrusion"
              {cx}
              cy={cy + radius * 0.28}
              r={radius * 1.04}
            />
            <circle
              class:map-board-fallback__node--trail={token.state === "trail"}
              class:map-board-fallback__node--discarded={token.state ===
                "discarded"}
              class:map-board-fallback__node--goal={token.state === "goal"}
              class:map-board-fallback__node--current={token.state ===
                "current"}
              class="map-board-fallback__node"
              {cx}
              {cy}
              r={radius}
            />
            <circle
              class="map-board-fallback__node-highlight"
              cx={cx - radius * 0.28}
              cy={cy - radius * 0.28}
              r={radius * 0.16}
            />
          </g>
        {/if}
      {/each}
    </svg>
  {/if}
</div>
