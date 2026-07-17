<script lang="ts">
  import type { Snippet } from "svelte";
  import type { SessionSnapshot } from "../api/types";
  import { buildMapBoard, type MapMoveChoice } from "../domain/map-board";
  import {
    inspectMapNode,
    isInspectableMapNode,
  } from "../domain/map-inspection";
  import {
    deriveMapTransition,
    initialMapTransition,
    type MapTransition,
  } from "../domain/map-transition";
  import GameMapWorld from "./GameMapWorld.svelte";
  import MapNodeInspector from "./MapNodeInspector.svelte";
  import type { MapInspectorAnchor } from "./map-inspector-position";
  import MapNavigationHelp from "./map-viewport/MapNavigationHelp.svelte";
  import NavigableMapViewport from "./map-viewport/NavigableMapViewport.svelte";

  let {
    session,
    busy = false,
    active = true,
    canGoBack = false,
    compassSelecting = false,
    onFollow,
    onBack,
    backDestinationLabel,
    onCompassSelect,
    railFooter,
  }: {
    session: SessionSnapshot;
    busy?: boolean;
    active?: boolean;
    canGoBack?: boolean;
    compassSelecting?: boolean;
    onFollow: (edgeToken: string) => void;
    onBack: () => void;
    backDestinationLabel?: string;
    onCompassSelect: (propertyId: string, entityQid: string) => void;
    railFooter?: Snippet;
  } = $props();

  let inspectedNodeId = $state<string | null>(null);
  let inspectorAnchor = $state<MapInspectorAnchor | null>(null);
  let board = $derived(buildMapBoard(session));
  let previousSession: SessionSnapshot | undefined;
  let previousBoard: ReturnType<typeof buildMapBoard> | undefined;
  let transition = $state<MapTransition>();
  let activeTransition = $derived(
    transition ?? initialMapTransition(board, session.state_version),
  );
  let viewportTransition = $derived({
    ...activeTransition,
    key: `${activeTransition.key}:active:${active}`,
  });
  let routeCount = $derived(board.choices.length);
  let inspection = $derived(
    inspectedNodeId ? (inspectMapNode(board, inspectedNodeId) ?? null) : null,
  );

  function choose(choice: MapMoveChoice): void {
    if (compassSelecting)
      onCompassSelect(choice.relation.property_id, choice.target.qid);
    else onFollow(choice.edge_token);
  }

  function inspect(nodeId: string, source: HTMLElement): void {
    const viewport = source.closest<HTMLElement>(".map-viewport");
    const node = source.closest<HTMLElement>("[data-map-node]") ?? source;
    if (viewport) {
      const viewportBounds = viewport.getBoundingClientRect();
      const nodeBounds = node.getBoundingClientRect();
      inspectorAnchor = {
        left: nodeBounds.left - viewportBounds.left,
        top: nodeBounds.top - viewportBounds.top,
        width: nodeBounds.width,
        height: nodeBounds.height,
      };
    } else inspectorAnchor = null;
    inspectedNodeId = nodeId;
  }

  function closeInspection(): void {
    inspectedNodeId = null;
    inspectorAnchor = null;
  }

  $effect(() => {
    const nextSession = session;
    const nextBoard = board;
    if (
      previousSession !== undefined &&
      previousBoard !== undefined &&
      nextSession !== previousSession
    ) {
      transition = deriveMapTransition(
        previousSession,
        nextSession,
        previousBoard,
        nextBoard,
      );
    } else if (previousSession === undefined) {
      transition = initialMapTransition(nextBoard, nextSession.state_version);
    }
    previousSession = nextSession;
    previousBoard = nextBoard;
  });

  $effect(() => {
    if (!inspectedNodeId) return;
    const node = board.nodes.find(({ id }) => id === inspectedNodeId);
    if (!node || !isInspectableMapNode(node)) inspectedNodeId = null;
  });
</script>

<section
  class="game-map"
  class:game-map--compass={compassSelecting}
  aria-labelledby="map-title"
  aria-describedby="map-instruction"
>
  <NavigableMapViewport
    {board}
    transition={viewportTransition}
    redrawKey={inspectedNodeId ?? "inspector-closed"}
    {railFooter}
  >
    {#snippet headerMain()}
      <div class="game-map__prompt">
        <p class="eyebrow">
          {compassSelecting
            ? "Compass ready"
            : routeCount === 0
              ? "Route exhausted"
              : "Your move"}
        </p>
        <h2 id="map-title">
          {compassSelecting
            ? "Which route should the Compass check?"
            : routeCount === 0
              ? canGoBack
                ? "This branch ends here"
                : "No route is available from this start"
              : "Where do you go next?"}
        </h2>
        <p
          id="map-instruction"
          class:game-map__instruction--compact={!compassSelecting &&
            routeCount > 0}
        >
          {compassSelecting
            ? "Select a connected entity to evaluate that relationship. This uses the Compass but does not move you."
            : routeCount === 0
              ? canGoBack
                ? `Retrace to ${backDestinationLabel ?? "the previous marker"}, then try another connection.`
                : "Return to the frontispiece and begin another round."
              : "Pick one connected entity. Drag or zoom the map to revisit every route you have explored."}
        </p>
      </div>
    {/snippet}

    {#snippet headerMeta()}
      <div class="game-map__header-meta">
        <p class="game-map__choice-count" aria-live="polite">
          <strong>{routeCount}</strong>
          {routeCount === 1 ? "route" : "routes"} in reach
        </p>
        <MapNavigationHelp />
      </div>
    {/snippet}

    <GameMapWorld
      {board}
      transition={activeTransition}
      {busy}
      {canGoBack}
      {compassSelecting}
      {onBack}
      {backDestinationLabel}
      onChoose={choose}
      onInspect={inspect}
    />

    {#snippet overlay()}
      <MapNodeInspector
        {inspection}
        anchor={inspectorAnchor}
        onClose={closeInspection}
      />
    {/snippet}
  </NavigableMapViewport>

  {#if session.last_connection}
    <p class="game-map__last-move" role="status">
      <strong>Last move</strong>
      <span>{session.last_connection}</span>
    </p>
  {/if}

  <ol class="game-map__trail">
    {#each board.trail as visit (visit.index)}
      <li
        aria-current={visit.index === board.trail.length - 1
          ? "step"
          : undefined}
      >
        {visit.index === 0 ? "Start" : `Move ${visit.index}`}: {visit.label}
        {#if visit.statement}
          — {visit.statement}{/if}
      </li>
    {/each}
  </ol>
</section>
