import { palette } from "@webwoven/design-tokens/tokens";
import {
  AmbientLight,
  BufferGeometry,
  CanvasTexture,
  CircleGeometry,
  Color,
  CylinderGeometry,
  DirectionalLight,
  Group,
  Line,
  LineBasicMaterial,
  Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  OrthographicCamera,
  PlaneGeometry,
  QuadraticBezierCurve3,
  RepeatWrapping,
  Scene,
  SphereGeometry,
  SRGBColorSpace,
  TorusGeometry,
  TubeGeometry,
  Vector3,
  WebGLRenderer,
  type Material,
  type Object3D,
} from "three";
import type { MapBoardLink, MapBoardNode } from "../domain/map-board";

const VIEW_HEIGHT = 6;
const SETTLE_DURATION_MS = 320;
const BOARD_DEPTH = -0.12;
const PATH_DEPTH = 0.02;
const NODE_DEPTH = 0.1;

type UnavailableHandler = () => void;

export class AtlasMapRenderer {
  readonly #scene = new Scene();
  readonly #camera = new OrthographicCamera();
  readonly #renderer: WebGLRenderer;
  readonly #unavailable: UnavailableHandler;
  #board = new Group();
  #nodes: readonly MapBoardNode[] = [];
  #links: readonly MapBoardLink[] = [];
  #viewWidth = VIEW_HEIGHT;
  #animationFrame: number | null = null;
  #settlingNodes: Object3D[] = [];
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

    this.#camera.position.set(0, 0, 10);
    this.#camera.lookAt(0, 0, 0);
    this.#scene.add(new AmbientLight(new Color(palette.paper), 2.7));
    const keyLight = new DirectionalLight(new Color(palette.paper), 2.4);
    keyLight.position.set(-3, 5, 8);
    this.#scene.add(keyLight, this.#board);
  }

  setBoard(
    nodes: readonly MapBoardNode[],
    links: readonly MapBoardLink[],
    reducedMotion: boolean,
  ): void {
    if (this.#disposed) return;
    this.#nodes = nodes;
    this.#links = links;
    this.#rebuildBoard(!reducedMotion);
  }

  resize(width: number, height: number): void {
    if (this.#disposed || width < 2 || height < 2) return;
    const aspect = width / height;
    this.#viewWidth = VIEW_HEIGHT * aspect;
    this.#camera.left = -this.#viewWidth / 2;
    this.#camera.right = this.#viewWidth / 2;
    this.#camera.top = VIEW_HEIGHT / 2;
    this.#camera.bottom = -VIEW_HEIGHT / 2;
    this.#camera.near = 0.1;
    this.#camera.far = 20;
    this.#camera.updateProjectionMatrix();
    this.#renderer.setSize(width, height, false);
    this.#rebuildBoard(false);
  }

  dispose(): void {
    if (this.#disposed) return;
    this.#disposed = true;
    this.#cancelAnimation();
    this.#renderer.domElement.removeEventListener(
      "webglcontextlost",
      this.#handleContextLost,
    );
    disposeObject(this.#board);
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

  #rebuildBoard(animate: boolean): void {
    this.#cancelAnimation();
    this.#scene.remove(this.#board);
    disposeObject(this.#board);
    this.#board = this.#createBoard();
    this.#scene.add(this.#board);

    if (animate && this.#settlingNodes.length > 0) {
      this.#settlingNodes.forEach((node) => node.scale.setScalar(0.76));
      this.#animateSettle();
      return;
    }
    this.#settlingNodes.forEach((node) => node.scale.setScalar(1));
    this.#render();
  }

  #createBoard(): Group {
    const board = new Group();
    this.#settlingNodes = [];
    board.add(this.#createPaperPlane(), ...this.#createContourLines());

    const nodesById = new Map(this.#nodes.map((node) => [node.id, node]));
    for (const link of this.#links) {
      const source = nodesById.get(link.source_node_id);
      const target = nodesById.get(link.target_node_id);
      if (source && target) board.add(this.#createPath(link, source, target));
    }
    for (const node of this.#nodes) {
      const marker = this.#createNodeMarker(node);
      board.add(marker);
      this.#settlingNodes.push(marker);
    }
    return board;
  }

  #createPaperPlane(): Mesh {
    const texture = createPaperTexture();
    texture.repeat.set(Math.max(2, this.#viewWidth / 2.4), 3);
    const material = new MeshStandardMaterial({
      color: new Color(palette.paper),
      map: texture,
      roughness: 0.96,
      metalness: 0,
    });
    const plane = new Mesh(
      new PlaneGeometry(this.#viewWidth * 0.99, VIEW_HEIGHT * 0.98),
      material,
    );
    plane.position.z = BOARD_DEPTH;
    return plane;
  }

  #createContourLines(): Line[] {
    const lines: Line[] = [];
    const left = -this.#viewWidth / 2;
    for (let row = 0; row < 6; row += 1) {
      const points: Vector3[] = [];
      for (let step = 0; step <= 16; step += 1) {
        const progress = step / 16;
        const x = left + progress * this.#viewWidth;
        const baseline = -2.25 + row * 0.9;
        const y = baseline + Math.sin(step * 0.72 + row * 1.4) * 0.1;
        points.push(new Vector3(x, y, BOARD_DEPTH + 0.01));
      }
      lines.push(
        new Line(
          new BufferGeometry().setFromPoints(points),
          new LineBasicMaterial({
            color: new Color(palette.mutedInk),
            transparent: true,
            opacity: 0.13,
          }),
        ),
      );
    }
    return lines;
  }

  #createPath(
    link: MapBoardLink,
    source: MapBoardNode,
    target: MapBoardNode,
  ): Group {
    const start = this.#pointFor(source, PATH_DEPTH);
    const end = this.#pointFor(target, PATH_DEPTH);
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const distance = Math.max(0.01, Math.hypot(dx, dy));
    const bend = stableBend(link.id) * Math.min(0.34, distance * 0.12);
    const control = new Vector3(
      (start.x + end.x) / 2 - (dy / distance) * bend,
      (start.y + end.y) / 2 + (dx / distance) * bend,
      PATH_DEPTH + 0.03,
    );
    const curve = new QuadraticBezierCurve3(start, control, end);
    const isTrail = link.kind === "trail";
    const color = isTrail ? palette.moss : palette.cartographic;
    const material = new MeshBasicMaterial({
      color: new Color(color),
      transparent: true,
      opacity: isTrail ? 0.78 : 0.48,
    });
    const path = new Mesh(
      new TubeGeometry(curve, 28, isTrail ? 0.025 : 0.016, 6, false),
      material,
    );
    const bead = new Mesh(
      new SphereGeometry(isTrail ? 0.055 : 0.04, 12, 8),
      material.clone(),
    );
    bead.position.copy(curve.getPoint(0.5));
    const group = new Group();
    group.add(path, bead);
    return group;
  }

  #createNodeMarker(node: MapBoardNode): Group {
    const position = this.#pointFor(node, NODE_DEPTH);
    const isCurrent = node.roles.includes("current");
    const radius = isCurrent ? 0.22 : 0.17;
    const color = markerColor(node);
    const group = new Group();
    group.position.copy(position);

    const shadow = new Mesh(
      new CircleGeometry(radius * 1.08, 32),
      new MeshBasicMaterial({
        color: new Color(palette.ink),
        transparent: true,
        opacity: 0.16,
      }),
    );
    shadow.position.set(0.045, -0.055, -0.055);

    const base = new Mesh(
      new CylinderGeometry(radius, radius * 1.05, 0.085, 32),
      new MeshStandardMaterial({
        color: new Color(color),
        roughness: 0.72,
        metalness: 0,
      }),
    );
    base.rotation.x = Math.PI / 2;

    const center = new Mesh(
      new CircleGeometry(radius * 0.37, 24),
      new MeshBasicMaterial({ color: new Color(palette.paper) }),
    );
    center.position.z = 0.048;
    group.add(shadow, base, center);

    if (isCurrent) {
      const ring = new Mesh(
        new TorusGeometry(radius * 1.38, 0.026, 8, 32),
        new MeshBasicMaterial({ color: new Color(palette.signal) }),
      );
      ring.position.z = -0.01;
      group.add(ring);
    }
    return group;
  }

  #pointFor(node: MapBoardNode, depth: number): Vector3 {
    return new Vector3(
      (node.position.x - 0.5) * this.#viewWidth,
      (0.5 - node.position.y) * VIEW_HEIGHT,
      depth + node.position.z * 0.08,
    );
  }

  #animateSettle(): void {
    const startedAt = performance.now();
    const tick = (now: number): void => {
      const progress = Math.min(1, (now - startedAt) / SETTLE_DURATION_MS);
      const eased = 1 - (1 - progress) ** 3;
      const scale = 0.76 + eased * 0.24;
      this.#settlingNodes.forEach((node) => node.scale.setScalar(scale));
      this.#render();
      if (progress < 1) this.#animationFrame = requestAnimationFrame(tick);
      else this.#animationFrame = null;
    };
    this.#animationFrame = requestAnimationFrame(tick);
  }

  #cancelAnimation(): void {
    if (this.#animationFrame !== null)
      cancelAnimationFrame(this.#animationFrame);
    this.#animationFrame = null;
  }

  #render(): void {
    this.#renderer.render(this.#scene, this.#camera);
  }
}

function markerColor(node: MapBoardNode): string {
  if (node.roles.includes("current")) return palette.signal;
  if (node.roles.includes("goal")) return palette.ochre;
  if (node.roles.includes("choice")) return palette.cartographic;
  if (node.roles.includes("trail")) return palette.moss;
  return palette.mutedInk;
}

function stableBend(id: string): number {
  let hash = 2166136261;
  for (const character of id) {
    hash ^= character.codePointAt(0) ?? 0;
    hash = Math.imul(hash, 16777619);
  }
  const magnitude = 0.55 + ((hash >>> 1) % 40) / 100;
  return (hash & 1) === 0 ? magnitude : -magnitude;
}

function createPaperTexture(): CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 96;
  canvas.height = 96;
  const context = canvas.getContext("2d");
  if (context) {
    context.fillStyle = palette.paper;
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = palette.mutedInk;
    context.globalAlpha = 0.055;
    for (let index = 0; index < 180; index += 1) {
      const x = (index * 37 + 11) % canvas.width;
      const y = (index * 61 + 23) % canvas.height;
      const size = index % 7 === 0 ? 2 : 1;
      context.fillRect(x, y, size, size);
    }
  }
  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace;
  texture.wrapS = RepeatWrapping;
  texture.wrapT = RepeatWrapping;
  return texture;
}

function disposeObject(object: Object3D): void {
  object.traverse((child) => {
    if (!(child instanceof Mesh) && !(child instanceof Line)) return;
    child.geometry.dispose();
    const materials = Array.isArray(child.material)
      ? child.material
      : [child.material];
    materials.forEach(disposeMaterial);
  });
  object.clear();
}

function disposeMaterial(material: Material): void {
  if (material instanceof MeshStandardMaterial) material.map?.dispose();
  material.dispose();
}
