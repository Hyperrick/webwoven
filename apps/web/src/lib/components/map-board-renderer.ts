import { palette } from "@webwoven/design-tokens/tokens";
import {
  AmbientLight,
  BackSide,
  BufferGeometry,
  CanvasTexture,
  CircleGeometry,
  Color,
  CylinderGeometry,
  DataTexture,
  DirectionalLight,
  Group,
  Line,
  LineBasicMaterial,
  Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  MeshToonMaterial,
  NearestFilter,
  OrthographicCamera,
  PlaneGeometry,
  QuadraticBezierCurve3,
  RedFormat,
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
const TOKEN_TILT = 0.38;
const TOKEN_SEGMENTS = 12;

type UnavailableHandler = () => void;

export class AtlasMapRenderer {
  readonly #scene = new Scene();
  readonly #camera = new OrthographicCamera();
  readonly #renderer: WebGLRenderer;
  readonly #unavailable: UnavailableHandler;
  readonly #toonRamp: DataTexture;
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
    this.#toonRamp = createToonRamp();
    this.#renderer.domElement.addEventListener(
      "webglcontextlost",
      this.#handleContextLost,
    );
    host.append(this.#renderer.domElement);

    this.#camera.position.set(0, 0, 10);
    this.#camera.lookAt(0, 0, 0);
    this.#scene.add(new AmbientLight(new Color(palette.paper), 0.45));
    const keyLight = new DirectionalLight(new Color(palette.paper), 3.2);
    keyLight.position.set(-4, 6, 8);
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
    this.#toonRamp.dispose();
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
    const isTrail = link.kind === "trail" || linkKindIs(link, "breadcrumb");
    const isDiscarded =
      linkKindIs(link, "discarded") || markerState(target) === "discarded";
    const color = isTrail
      ? palette.moss
      : isDiscarded
        ? palette.mutedInk
        : palette.cartographic;
    const material = new MeshBasicMaterial({
      color: new Color(color),
      transparent: true,
      opacity: isTrail ? 0.82 : isDiscarded ? 0.2 : 0.48,
    });
    const pathRadius = isTrail ? 0.027 : isDiscarded ? 0.012 : 0.017;
    const path = new Mesh(
      new TubeGeometry(curve, 28, pathRadius, 6, false),
      material,
    );
    const bead = new Mesh(
      new SphereGeometry(isTrail ? 0.058 : isDiscarded ? 0.03 : 0.042, 12, 8),
      material.clone(),
    );
    bead.position.copy(curve.getPoint(0.5));
    const group = new Group();
    if (isTrail) {
      const outline = new Mesh(
        new TubeGeometry(curve, 28, pathRadius + 0.011, 6, false),
        new MeshBasicMaterial({
          color: new Color(palette.ink),
          transparent: true,
          opacity: 0.34,
        }),
      );
      group.add(outline);
    }
    group.add(path, bead);
    return group;
  }

  #createNodeMarker(node: MapBoardNode): Group {
    const position = this.#pointFor(node, NODE_DEPTH);
    const state = markerState(node);
    const isCurrent = state === "current";
    const isDiscarded = state === "discarded";
    const radius = markerRadius(state);
    const depth = isCurrent ? 0.18 : 0.15;
    const color = markerColor(node);
    const group = new Group();
    group.position.copy(position);

    const shadow = new Mesh(
      new CircleGeometry(radius * 1.16, 24),
      new MeshBasicMaterial({
        color: new Color(palette.ink),
        transparent: true,
        opacity: isDiscarded ? 0.08 : 0.2,
      }),
    );
    shadow.position.set(0.065, -0.085, -0.055);
    shadow.scale.y = 0.48;

    const token = new Group();
    token.rotation.x = Math.PI / 2 - TOKEN_TILT;
    token.rotation.z = stableMarkerTurn(node.qid);
    const tokenGeometry = new CylinderGeometry(
      radius,
      radius * 1.06,
      depth,
      TOKEN_SEGMENTS,
    );
    const outline = new Mesh(
      tokenGeometry,
      new MeshBasicMaterial({
        color: new Color(palette.ink),
        side: BackSide,
        transparent: isDiscarded,
        opacity: isDiscarded ? 0.58 : 1,
      }),
    );
    outline.scale.set(1.075, 1.055, 1.075);

    const base = new Mesh(
      tokenGeometry,
      new MeshToonMaterial({
        color: new Color(color),
        gradientMap: this.#toonRamp,
      }),
    );

    const center = new Mesh(
      new CircleGeometry(radius * 0.33, TOKEN_SEGMENTS),
      new MeshBasicMaterial({
        color: new Color(palette.paper),
        transparent: isDiscarded,
        opacity: isDiscarded ? 0.55 : 1,
      }),
    );
    center.rotation.x = -Math.PI / 2;
    center.position.y = depth / 2 + 0.006;
    token.add(outline, base, center);
    group.add(shadow, token);

    if (isCurrent) {
      const ringOutline = new Mesh(
        new TorusGeometry(radius * 1.38, 0.038, 8, 32),
        new MeshBasicMaterial({ color: new Color(palette.ink) }),
      );
      const ring = new Mesh(
        new TorusGeometry(radius * 1.38, 0.023, 8, 32),
        new MeshBasicMaterial({ color: new Color(palette.signal) }),
      );
      for (const item of [ringOutline, ring]) {
        item.rotation.x = -Math.PI / 2;
        item.position.y = depth / 2 + 0.01;
      }
      ring.position.y += 0.006;
      token.add(ringOutline, ring);
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

type MarkerState = "current" | "goal" | "choice" | "breadcrumb" | "discarded";

function markerState(node: MapBoardNode): MarkerState {
  if (hasRole(node, "current")) return "current";
  if (hasRole(node, "discarded")) return "discarded";
  if (hasRole(node, "goal")) return "goal";
  if (hasAnyRole(node, ["trail", "breadcrumb", "visited"])) return "breadcrumb";
  if (hasRole(node, "choice")) return "choice";
  return "discarded";
}

function markerColor(node: MapBoardNode): string {
  const state = markerState(node);
  if (state === "current") return palette.signal;
  if (state === "goal") return palette.ochre;
  if (state === "choice") return palette.cartographic;
  if (state === "breadcrumb") return palette.moss;
  return palette.mutedInk;
}

function markerRadius(state: MarkerState): number {
  if (state === "current") return 0.23;
  if (state === "goal") return 0.2;
  if (state === "choice") return 0.18;
  if (state === "breadcrumb") return 0.175;
  return 0.15;
}

function hasRole(node: MapBoardNode, role: string): boolean {
  return (node.roles as readonly string[]).includes(role);
}

function hasAnyRole(node: MapBoardNode, roles: readonly string[]): boolean {
  return roles.some((role) => hasRole(node, role));
}

function linkKindIs(link: MapBoardLink, kind: string): boolean {
  return String(link.kind) === kind;
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

function stableMarkerTurn(id: string): number {
  let hash = 2166136261;
  for (const character of id) {
    hash ^= character.codePointAt(0) ?? 0;
    hash = Math.imul(hash, 16777619);
  }
  return (((hash >>> 0) % 9) - 4) * 0.012;
}

function createToonRamp(): DataTexture {
  const texture = new DataTexture(
    new Uint8Array([48, 152, 255]),
    3,
    1,
    RedFormat,
  );
  texture.minFilter = NearestFilter;
  texture.magFilter = NearestFilter;
  texture.generateMipmaps = false;
  texture.needsUpdate = true;
  return texture;
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
  const geometries = new Set<BufferGeometry>();
  const materials = new Set<Material>();
  object.traverse((child) => {
    if (!(child instanceof Mesh) && !(child instanceof Line)) return;
    geometries.add(child.geometry);
    const childMaterials = Array.isArray(child.material)
      ? child.material
      : [child.material];
    childMaterials.forEach((material) => materials.add(material));
  });
  geometries.forEach((geometry) => geometry.dispose());
  materials.forEach(disposeMaterial);
  object.clear();
}

function disposeMaterial(material: Material): void {
  if (material instanceof MeshStandardMaterial) material.map?.dispose();
  material.dispose();
}
