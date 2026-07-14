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
import {
  isRenderableMapCameraView,
  mapCameraViewsEqual,
  visibleMapCameraRect,
  type MapCameraView,
} from "../map-camera/map-camera-view";
import { AtlasBoardScene } from "./map-board-scene";

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
  #nodes: readonly MapBoardNode[] | null = null;
  #links: readonly MapBoardLink[] | null = null;
  #worldWidth = 0;
  #worldHeight = 0;
  #view: MapCameraView | null = null;
  #animationFrame: number | null = null;
  #disposed = false;

  constructor(host: HTMLElement, unavailable: UnavailableHandler) {
    this.#unavailable = unavailable;
    this.#renderer = new WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: "low-power",
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
  ): void {
    if (this.#disposed) return;
    const boardChanged =
      nodes !== this.#nodes ||
      links !== this.#links ||
      worldWidth !== this.#worldWidth ||
      worldHeight !== this.#worldHeight;
    if (!boardChanged) {
      if (reducedMotion) this.#finishSettleAnimation();
      return;
    }
    if (worldWidth <= 0 || worldHeight <= 0) return;

    this.#nodes = nodes;
    this.#links = links;
    this.#worldWidth = worldWidth;
    this.#worldHeight = worldHeight;
    this.#replaceBoard(!reducedMotion);
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

  #replaceBoard(animate: boolean): void {
    this.#cancelAnimation();
    this.#disposeBoard();
    this.#board = new AtlasBoardScene(
      this.#nodes ?? [],
      this.#links ?? [],
      this.#worldWidth,
      this.#worldHeight,
    );
    this.#scene.add(this.#board.root);

    if (animate && this.#board.settlingNodes.length > 0) {
      this.#board.settlingNodes.forEach((node) => node.scale.setScalar(0.76));
      this.#animateSettle(this.#board.settlingNodes);
      return;
    }
    this.#board.settlingNodes.forEach((node) => node.scale.setScalar(1));
    this.#render();
  }

  #disposeBoard(): void {
    if (!this.#board) return;
    this.#scene.remove(this.#board.root);
    this.#board.dispose();
    this.#board = null;
  }

  #animateSettle(nodes: readonly Object3D[]): void {
    const startedAt = performance.now();
    const tick = (now: number): void => {
      const progress = Math.min(1, (now - startedAt) / SETTLE_DURATION_MS);
      const eased = 1 - (1 - progress) ** 3;
      const scale = 0.76 + eased * 0.24;
      nodes.forEach((node) => node.scale.setScalar(scale));
      this.#render();
      if (progress < 1) this.#animationFrame = requestAnimationFrame(tick);
      else this.#animationFrame = null;
    };
    this.#animationFrame = requestAnimationFrame(tick);
  }

  #finishSettleAnimation(): void {
    if (this.#animationFrame === null) return;
    this.#cancelAnimation();
    this.#board?.settlingNodes.forEach((node) => node.scale.setScalar(1));
    this.#render();
  }

  #cancelAnimation(): void {
    if (this.#animationFrame !== null)
      cancelAnimationFrame(this.#animationFrame);
    this.#animationFrame = null;
  }

  #render(): void {
    if (!this.#view) return;
    this.#renderer.render(this.#scene, this.#camera);
  }
}
