<script lang="ts">
  import { onMount, tick, type Snippet } from "svelte";
  import type { MapBoard } from "../../domain/map-board";
  import type { MapTransition } from "../../domain/map-transition";
  import {
    MAP_MAX_ZOOM,
    cameraForBounds,
    cameraView,
    clampCamera,
    ensureBoundsVisible,
    gestureCamera,
    minimumMapZoom,
    panCamera,
    panCameraToWorldPoint,
    panCameraToWorldX,
    panCameraToWorldY,
    zoomCameraAt,
    type MapCameraEnvironment,
    type MapCameraState,
    type MapPoint,
    type MapWorldRect,
  } from "../../map-camera/map-camera";
  import { attachMapGestures } from "../../map-camera/map-gestures";
  import { shouldReduceMotion } from "../../preferences/preferences";
  import MapBoardCanvas from "../MapBoardCanvas.svelte";
  import MapViewportControls from "./MapViewportControls.svelte";

  let {
    board,
    transition,
    redrawKey = "",
    children,
    overlay,
    headerMain,
    headerMeta,
    railFooter,
    verticalFlow = false,
    activePreviewNodeId = null,
  }: {
    board: MapBoard;
    transition: MapTransition;
    redrawKey?: string;
    children: Snippet;
    overlay?: Snippet;
    headerMain?: Snippet;
    headerMeta?: Snippet;
    railFooter?: Snippet;
    verticalFlow?: boolean;
    activePreviewNodeId?: string | null;
  } = $props();

  let viewport: HTMLDivElement;
  let world: HTMLDivElement;
  let ready = $state(false);
  let positioned = $state(false);
  let panning = $state(false);
  let camera = $state<MapCameraState>({ x: 0, y: 0, zoom: 1 });
  let viewportSize = $state({ width: 1, height: 1 });
  let worldSize = $state({ width: 1, height: 1 });
  let environment = $derived<MapCameraEnvironment>({
    viewport: viewportSize,
    world: worldSize,
  });
  let minimumZoom = $derived(minimumMapZoom(environment));
  let view = $derived(cameraView(camera, environment));
  let worldStyle = $derived(
    `width: ${board.layout.width_units}rem; height: ${board.layout.height_units}rem; transform: translate3d(${camera.x}px, ${camera.y}px, 0) scale(${camera.zoom})`,
  );
  let cameraAnimationFrame: number | undefined;
  let positioningVersion = 0;

  onMount(() => {
    const measure = (): void => {
      viewportSize = {
        width: Math.max(1, viewport.clientWidth),
        height: Math.max(1, viewport.clientHeight),
      };
      worldSize = {
        width: Math.max(1, world.offsetWidth),
        height: Math.max(1, world.offsetHeight),
      };
      if (positioned) camera = clampCamera(camera, currentEnvironment());
    };
    const observer = new ResizeObserver(measure);
    observer.observe(viewport);
    observer.observe(world);
    measure();
    const detachGestures = attachMapGestures(viewport, {
      panBy: (delta) =>
        setCamera(panCamera(camera, delta, currentEnvironment())),
      transformAt: (previous, next, factor) =>
        setCamera(
          gestureCamera(camera, previous, next, factor, currentEnvironment()),
        ),
      zoomAt: (anchor, factor) => zoomAt(anchor, factor),
      fitMap,
      focusCurrent,
      setPanning: (active) => (panning = active),
    });
    ready = true;
    return () => {
      ready = false;
      cancelCameraAnimation();
      observer.disconnect();
      detachGestures();
    };
  });

  $effect(() => {
    const version = ++positioningVersion;
    const nextFocus = transition.key;
    const nextBoard = board;
    if (!ready) return;
    void nextFocus;
    void nextBoard;
    void tick().then(() => {
      if (!ready || version !== positioningVersion) return;
      refreshWorldSize();
      if (!positioned) {
        fitActive();
        positioned = true;
      } else panToActiveStage(transition);
    });
  });

  $effect(() => {
    const previewNodeId = activePreviewNodeId;
    if (!ready || !previewNodeId) return;
    void tick().then(() => revealPreviewNode(previewNodeId));
  });

  function currentEnvironment(): MapCameraEnvironment {
    return { viewport: viewportSize, world: worldSize };
  }

  function refreshWorldSize(): void {
    worldSize = {
      width: Math.max(1, world.offsetWidth),
      height: Math.max(1, world.offsetHeight),
    };
  }

  function setCamera(next: MapCameraState): void {
    cancelCameraAnimation();
    camera = next;
  }

  function animateCameraTo(next: MapCameraState, duration = 320): void {
    cancelCameraAnimation();
    if (shouldReduceMotion()) {
      camera = next;
      return;
    }
    const start = { ...camera };
    const startedAt = performance.now();
    const step = (now: number): void => {
      if (shouldReduceMotion()) {
        camera = next;
        cameraAnimationFrame = undefined;
        return;
      }
      const progress = Math.min(1, (now - startedAt) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      camera = {
        x: start.x + (next.x - start.x) * eased,
        y: start.y + (next.y - start.y) * eased,
        zoom: start.zoom + (next.zoom - start.zoom) * eased,
      };
      if (progress < 1) cameraAnimationFrame = requestAnimationFrame(step);
      else cameraAnimationFrame = undefined;
    };
    cameraAnimationFrame = requestAnimationFrame(step);
  }

  function cancelCameraAnimation(): void {
    if (cameraAnimationFrame === undefined) return;
    cancelAnimationFrame(cameraAnimationFrame);
    cameraAnimationFrame = undefined;
  }

  function zoomAt(anchor: MapPoint, factor: number): void {
    setCamera(
      zoomCameraAt(camera, camera.zoom * factor, anchor, currentEnvironment()),
    );
  }

  function fitMap(): void {
    const bounds = boundsFor("[data-map-node]");
    if (!bounds) return;
    setCamera(
      cameraForBounds(bounds, currentEnvironment(), {
        padding: 36,
        maximumZoom: 1,
      }),
    );
  }

  function fitActive(): void {
    const bounds = boundsFor(initialFocusSelector());
    if (!bounds) return;
    const fitted = cameraForBounds(bounds, currentEnvironment(), {
      padding: 44,
      maximumZoom: 1,
    });
    if (!isNarrowViewport()) {
      setCamera(fitted);
      return;
    }
    const minimumReadableZoom = viewportSize.width <= 360 ? 0.56 : 0.65;
    const readable =
      fitted.zoom < minimumReadableZoom
        ? zoomCameraAt(
            fitted,
            minimumReadableZoom,
            { x: viewportSize.width / 2, y: viewportSize.height / 2 },
            currentEnvironment(),
          )
        : fitted;
    setCamera(ensureActiveFrontierVisible(readable));
  }

  function focusCurrent(): void {
    const bounds = currentBoundsFor(transition.to_node_id);
    if (!bounds) return;
    setCamera(
      cameraForBounds(bounds, currentEnvironment(), {
        padding: Math.min(140, viewportSize.width * 0.28),
        maximumZoom: 1.1,
      }),
    );
  }

  function panToActiveStage(nextTransition: MapTransition): void {
    const currentBounds = currentBoundsFor(nextTransition.to_node_id);
    if (!currentBounds) return;
    if (nextTransition.kind === "dead_end_back") return;
    if (nextTransition.kind === "back") {
      const worldPoint = {
        x: (currentBounds.left + currentBounds.right) / 2,
        y: (currentBounds.top + currentBounds.bottom) / 2,
      };
      animateCameraTo(
        panCameraToWorldPoint(
          camera,
          worldPoint,
          { x: viewportSize.width / 2, y: viewportSize.height / 2 },
          currentEnvironment(),
        ),
        440,
      );
      return;
    }
    const currentCenterX = (currentBounds.left + currentBounds.right) / 2;
    const currentCenterY = (currentBounds.top + currentBounds.bottom) / 2;
    if (verticalFlow) {
      const screenAnchorY = Math.min(180, viewportSize.height * 0.28);
      const anchored = panCameraToWorldY(
        camera,
        currentCenterY,
        screenAnchorY,
        currentEnvironment(),
      );
      animateCameraTo(ensureVerticalActiveStageVisible(anchored));
      return;
    }
    const screenAnchorX = Math.min(280, viewportSize.width * 0.28);
    const anchored = panCameraToWorldX(
      camera,
      currentCenterX,
      screenAnchorX,
      currentEnvironment(),
    );
    const withCurrentVisible = isNarrowViewport()
      ? anchored
      : ensureBoundsVisible(anchored, currentBounds, currentEnvironment(), 28);
    animateCameraTo(ensureActiveFrontierVisible(withCurrentVisible));
  }

  function ensureActiveFrontierVisible(next: MapCameraState): MapCameraState {
    const frontierBounds = boundsFor("[data-map-near-focus]");
    return frontierBounds
      ? ensureBoundsVisible(next, frontierBounds, currentEnvironment(), 16)
      : next;
  }

  function ensureVerticalActiveStageVisible(
    next: MapCameraState,
  ): MapCameraState {
    const activeStageBounds = boundsFor(
      '[data-map-back-target="true"], [data-map-current], [data-mobile-choice-node], [data-map-near-focus="dead-end"]',
    );
    return activeStageBounds
      ? ensureBoundsVisible(next, activeStageBounds, currentEnvironment(), 16)
      : next;
  }

  function boundsFor(selector: string): MapWorldRect | null {
    const elements = [...world.querySelectorAll<HTMLElement>(selector)];
    if (elements.length === 0) return null;
    return elements.map(worldBoundsFor).reduce(combineBounds);
  }

  function currentBoundsFor(nodeId: string): MapWorldRect | null {
    const elements = [
      ...world.querySelectorAll<HTMLElement>("[data-map-current]"),
    ].filter((element) => element.dataset.mapNodeId === nodeId);
    if (elements.length === 0) return null;
    return elements.map(worldBoundsFor).reduce(combineBounds);
  }

  function worldBoundsFor(element: HTMLElement): MapWorldRect {
    const viewportBounds = viewport.getBoundingClientRect();
    const originLeft = viewportBounds.left + viewport.clientLeft;
    const originTop = viewportBounds.top + viewport.clientTop;
    const bounds = element.getBoundingClientRect();
    const renderedCamera = renderedWorldCamera();
    return {
      left: (bounds.left - originLeft - renderedCamera.x) / renderedCamera.zoom,
      top: (bounds.top - originTop - renderedCamera.y) / renderedCamera.zoom,
      right:
        (bounds.right - originLeft - renderedCamera.x) / renderedCamera.zoom,
      bottom:
        (bounds.bottom - originTop - renderedCamera.y) / renderedCamera.zoom,
    };
  }

  function renderedWorldCamera(): MapCameraState {
    const transform = getComputedStyle(world).transform;
    if (transform === "none") return { x: 0, y: 0, zoom: 1 };
    const matrix = new DOMMatrixReadOnly(transform);
    return {
      x: Number.isFinite(matrix.e) ? matrix.e : camera.x,
      y: Number.isFinite(matrix.f) ? matrix.f : camera.y,
      zoom: Number.isFinite(matrix.a) && matrix.a > 0 ? matrix.a : camera.zoom,
    };
  }

  function combineBounds(
    combined: MapWorldRect,
    rectangle: MapWorldRect,
  ): MapWorldRect {
    return {
      left: Math.min(combined.left, rectangle.left),
      top: Math.min(combined.top, rectangle.top),
      right: Math.max(combined.right, rectangle.right),
      bottom: Math.max(combined.bottom, rectangle.bottom),
    };
  }

  function revealFocusedNode(event: FocusEvent): void {
    const target = event.target;
    if (!(target instanceof Element)) return;
    if (!target.matches(":focus-visible")) return;
    const node = target.closest<HTMLElement>("[data-map-node]");
    if (!node || !world.contains(node)) return;
    setCamera(
      ensureBoundsVisible(
        camera,
        worldBoundsFor(node),
        currentEnvironment(),
        28,
      ),
    );
  }

  function revealPreviewNode(nodeId: string): void {
    if (!ready || activePreviewNodeId !== nodeId) return;
    const node = [
      ...world.querySelectorAll<HTMLElement>("[data-map-node]"),
    ].find((candidate) => candidate.dataset.mapNodeId === nodeId);
    const detail = viewport.querySelector<HTMLElement>(
      "[data-mobile-choice-detail]",
    );
    if (!node || !detail) return;
    const nodeBounds = node.getBoundingClientRect();
    const detailBounds = detail.getBoundingClientRect();
    const controlsBounds = viewport
      .querySelector<HTMLElement>(".map-viewport-controls--canvas")
      ?.getBoundingClientRect();
    const viewportBounds = viewport.getBoundingClientRect();
    const safeTop = (controlsBounds?.bottom ?? viewportBounds.top) + 2;
    const safeBottom = detailBounds.top - 2;
    const safeHeight = Math.max(0, safeBottom - safeTop);
    let deltaY = 0;
    if (nodeBounds.height > safeHeight) {
      deltaY =
        (safeTop + safeBottom) / 2 - (nodeBounds.top + nodeBounds.bottom) / 2;
    } else if (nodeBounds.top < safeTop) {
      deltaY = safeTop - nodeBounds.top;
    } else if (nodeBounds.bottom > safeBottom) {
      deltaY = safeBottom - nodeBounds.bottom;
    }
    if (Math.abs(deltaY) < 1) return;
    animateCameraTo(
      panCamera(camera, { x: 0, y: deltaY }, currentEnvironment()),
      200,
    );
  }

  function initialFocusSelector(): string {
    return isNarrowViewport()
      ? "[data-map-current], [data-map-near-focus]"
      : "[data-map-focus]";
  }

  function isNarrowViewport(): boolean {
    return viewportSize.width <= 600;
  }

  function zoomOut(): void {
    zoomAt({ x: viewportSize.width / 2, y: viewportSize.height / 2 }, 1 / 1.2);
  }

  function zoomIn(): void {
    zoomAt({ x: viewportSize.width / 2, y: viewportSize.height / 2 }, 1.2);
  }
</script>

<div class="game-map__frame">
  <header class="game-map__header">
    {#if headerMain}{@render headerMain()}{/if}
    <div class="game-map__header-tools">
      {#if headerMeta}{@render headerMeta()}{/if}
    </div>
  </header>

  <div class="map-viewport-layout">
    <div class="map-utility-rail">
      <div class="map-utility-rail__navigation">
        <MapViewportControls
          placement="rail"
          zoom={camera.zoom}
          {minimumZoom}
          maximumZoom={MAP_MAX_ZOOM}
          onZoomOut={zoomOut}
          onZoomIn={zoomIn}
          onFitMap={fitMap}
          onFocusCurrent={focusCurrent}
        />
      </div>
      {#if railFooter}
        <div class="map-utility-rail__hints">
          {@render railFooter()}
        </div>
      {/if}
    </div>

    <!-- svelte-ignore a11y_no_noninteractive_tabindex (keyboard-navigable spatial canvas) -->
    <div
      class="game-map__viewport map-viewport"
      class:map-viewport--panning={panning}
      role="region"
      aria-label="Exploration map"
      data-map-layout={verticalFlow ? "vertical" : "horizontal"}
      data-map-presentation={verticalFlow ? "constellation" : "cards"}
      aria-describedby="map-viewport-instructions"
      tabindex="0"
      bind:this={viewport}
      onfocusin={revealFocusedNode}
    >
      <MapBoardCanvas {board} {view} {transition} {redrawKey} />
      <div
        class="game-map__surface map-viewport__world"
        style={worldStyle}
        bind:this={world}
      >
        {@render children()}
      </div>

      <MapViewportControls
        placement="canvas"
        zoom={camera.zoom}
        {minimumZoom}
        maximumZoom={MAP_MAX_ZOOM}
        onZoomOut={zoomOut}
        onZoomIn={zoomIn}
        onFitMap={fitMap}
        onFocusCurrent={focusCurrent}
      />

      <p id="map-viewport-instructions" class="map-viewport__instructions">
        Drag to pan · pinch or scroll to zoom · keyboard: arrows pan, +/− zoom,
        0 fits the map, Home returns to current
      </p>
      {#if overlay}{@render overlay()}{/if}
    </div>
  </div>
</div>
