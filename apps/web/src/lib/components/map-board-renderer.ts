import { palette } from "@webwoven/design-tokens/tokens";
import {
  AmbientLight,
  Color,
  DirectionalLight,
  OrthographicCamera,
  Scene,
  SRGBColorSpace,
  WebGLRenderer,
  type Object3D,
} from "three";
import type { MapBoardLink, MapBoardNode } from "../domain/map-board";
import type { MapTransition } from "../domain/map-transition";
import {
  isRenderableMapCameraView,
  mapCameraViewsEqual,
  visibleMapCameraRect,
  type MapCameraView,
} from "../map-camera/map-camera-view";
import { AtlasBoardScene, disposeSceneObject } from "./map-board-scene";

const SETTLE_DURATION_MS = 320;
const CAMERA_DEPTH = 1_000;

type UnavailableHandler = () => void;

/** Coordinates a viewport-sized WebGL renderer and an immutable world scene. */
export class AtlasMapRenderer {
  readonly #scene = new Scene();
  readonly #camera = new OrthographicCamera();
  readonly #renderer: WebGLRenderer;
  readonly #unavailable: UnavailableHandler;
  #board: AtlasBoardScene | null = null;
  #retiredBoard: AtlasBoardScene | null = null;
  #fadingMarker: Object3D | null = null;
  #nodes: readonly MapBoardNode[] | null = null;
  #links: readonly MapBoardLink[] | null = null;
  #worldWidth = 0;
  #worldHeight = 0;
  #markerScale = 1;
  #view: MapCameraView | null = null;
  #animationFrame: number | null = null;
  #disposed = false;

  constructor(host: HTMLElement, unavailable: UnavailableHandler) {
    this.#unavailable = unavailable;
    this.#renderer = new WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: "low-power",
      // The map is mostly static. Preserve its last frame so embedded browsers
      // cannot discard the paper, routes, and markers while another tab or a
      // backdrop-filter layer is active.
      preserveDrawingBuffer: true,
    });
    this.#renderer.outputColorSpace = SRGBColorSpace;
    this.#renderer.setClearAlpha(0);
    this.#renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    this.#renderer.domElement.addEventListener(
      "webglcontextlost",
      this.#handleContextLost,
    );
    host.append(this.#renderer.domElement);

    this.#camera.position.set(0, 0, CAMERA_DEPTH);
    this.#camera.lookAt(0, 0, 0);
    this.#camera.near = 0.1;
    this.#camera.far = CAMERA_DEPTH * 2;
    this.#scene.add(new AmbientLight(new Color(palette.paper), 0.45));
    const keyLight = new DirectionalLight(new Color(palette.paper), 3.2);
    keyLight.position.set(-4, 6, 8);
    this.#scene.add(keyLight);
  }

  setBoard(
    nodes: readonly MapBoardNode[],
    links: readonly MapBoardLink[],
    worldWidth: number,
    worldHeight: number,
    reducedMotion: boolean,
    transition: MapTransition,
    markerScale = 1,
  ): void {
    if (this.#disposed) return;
    const boardChanged =
      nodes !== this.#nodes ||
      links !== this.#links ||
      worldWidth !== this.#worldWidth ||
      worldHeight !== this.#worldHeight ||
      markerScale !== this.#markerScale;
    if (!boardChanged) {
      if (reducedMotion) this.#finishSettleAnimation();
      return;
    }
    if (worldWidth <= 0 || worldHeight <= 0) return;

    this.#nodes = nodes;
    this.#links = links;
    this.#worldWidth = worldWidth;
    this.#worldHeight = worldHeight;
    this.#markerScale = markerScale;
    this.#replaceBoard(!reducedMotion, transition);
  }

  /** Updates only renderer size and camera projection; scene geometry is retained. */
  setCameraView(view: MapCameraView): void {
    if (
      this.#disposed ||
      !isRenderableMapCameraView(view) ||
      mapCameraViewsEqual(this.#view, view)
    )
      return;

    const viewportChanged =
      this.#view?.viewport_width !== view.viewport_width ||
      this.#view?.viewport_height !== view.viewport_height;
    this.#view = { ...view };
    if (viewportChanged) {
      this.#renderer.setSize(view.viewport_width, view.viewport_height, false);
    }

    const visible = visibleMapCameraRect(view);
    this.#camera.left = visible.x;
    this.#camera.right = visible.x + visible.width;
    this.#camera.top = -visible.y;
    this.#camera.bottom = -(visible.y + visible.height);
    this.#camera.updateProjectionMatrix();
    this.#render();
  }

  /** Redraws the retained scene after the browser restores this tab. */
  refresh(): void {
    if (this.#disposed) return;
    this.#render();
  }

  dispose(): void {
    if (this.#disposed) return;
    this.#disposed = true;
    this.#cancelAnimation();
    this.#renderer.domElement.removeEventListener(
      "webglcontextlost",
      this.#handleContextLost,
    );
    this.#disposeBoard();
    this.#scene.clear();
    this.#renderer.dispose();
    this.#renderer.domElement.remove();
  }

  readonly #handleContextLost = (event: Event): void => {
    event.preventDefault();
    this.#cancelAnimation();
    this.#renderer.domElement.hidden = true;
    this.#unavailable();
  };

  #replaceBoard(animate: boolean, transition: MapTransition): void {
    this.#cancelAnimation();
    this.#disposeRetiredBoard();
    const previous = this.#board;
    this.#board = null;
    const fadingMarker =
      animate &&
      (transition.kind === "back" || transition.kind === "dead_end_back") &&
      transition.from_node_id
        ? previous?.detachMarker(transition.from_node_id)
        : undefined;
    if (previous) this.#scene.remove(previous.root);
    if (fadingMarker && previous) {
      this.#retiredBoard = previous;
      this.#fadingMarker = fadingMarker;
      this.#scene.add(fadingMarker);
    } else {
      previous?.dispose();
    }
    this.#board = new AtlasBoardScene(
      this.#nodes ?? [],
      this.#links ?? [],
      this.#worldWidth,
      this.#worldHeight,
      this.#markerScale,
    );
    this.#scene.add(this.#board.root);

    if (animate && transition.kind === "dead_end_back" && fadingMarker) {
      this.#board.settlingNodes.forEach((node) => node.scale.setScalar(1));
      this.#animateMarkerFade(fadingMarker);
      return;
    }
    if (animate && this.#board.settlingNodes.length > 0) {
      this.#board.settlingNodes.forEach((node) => node.scale.setScalar(0.76));
      this.#animateSettle(this.#board.settlingNodes, fadingMarker);
      return;
    }
    this.#board.settlingNodes.forEach((node) => node.scale.setScalar(1));
    this.#render();
  }

  #animateMarkerFade(marker: Object3D): void {
    const startedAt = performance.now();
    const duration = 220;
    const tick = (now: number): void => {
      const progress = Math.min(1, (now - startedAt) / duration);
      setObjectOpacity(marker, 1 - progress);
      this.#render();
      if (progress < 1) this.#animationFrame = requestAnimationFrame(tick);
      else {
        this.#animationFrame = null;
        this.#disposeRetiredBoard();
      }
    };
    this.#animationFrame = requestAnimationFrame(tick);
  }

  #disposeBoard(): void {
    this.#disposeRetiredBoard();
    if (!this.#board) return;
    this.#scene.remove(this.#board.root);
    this.#board.dispose();
    this.#board = null;
  }

  #animateSettle(nodes: readonly Object3D[], fadingMarker?: Object3D): void {
    const startedAt = performance.now();
    const duration = fadingMarker ? 440 : SETTLE_DURATION_MS;
    const tick = (now: number): void => {
      const progress = Math.min(1, (now - startedAt) / duration);
      const eased = 1 - (1 - progress) ** 3;
      const scale = 0.76 + eased * 0.24;
      nodes.forEach((node) => node.scale.setScalar(scale));
      if (fadingMarker) setObjectOpacity(fadingMarker, 1 - progress);
      this.#render();
      if (progress < 1) this.#animationFrame = requestAnimationFrame(tick);
      else {
        this.#animationFrame = null;
        this.#disposeRetiredBoard();
      }
    };
    this.#animationFrame = requestAnimationFrame(tick);
  }

  #finishSettleAnimation(): void {
    if (this.#animationFrame === null) return;
    this.#cancelAnimation();
    this.#board?.settlingNodes.forEach((node) => node.scale.setScalar(1));
    this.#disposeRetiredBoard();
    this.#render();
  }

  #cancelAnimation(): void {
    if (this.#animationFrame !== null)
      cancelAnimationFrame(this.#animationFrame);
    this.#animationFrame = null;
  }

  #disposeRetiredBoard(): void {
    if (this.#fadingMarker) {
      this.#scene.remove(this.#fadingMarker);
      disposeSceneObject(this.#fadingMarker);
      this.#fadingMarker = null;
    }
    this.#retiredBoard?.dispose();
    this.#retiredBoard = null;
  }

  #render(): void {
    if (!this.#view) return;
    this.#renderer.render(this.#scene, this.#camera);
  }
}

function setObjectOpacity(object: Object3D, opacity: number): void {
  object.traverse((child) => {
    if (!("material" in child)) return;
    const value = child as Object3D & {
      material: { opacity: number; transparent: boolean; userData: object };
    };
    const material = value.material;
    const userData = material.userData as { baseOpacity?: number };
    const base = userData.baseOpacity ?? material.opacity;
    userData.baseOpacity = base;
    material.transparent = true;
    material.opacity = base * Math.max(0, opacity);
  });
}
