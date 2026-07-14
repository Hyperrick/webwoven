import { palette } from "@webwoven/design-tokens/tokens";
import {
  BackSide,
  BufferGeometry,
  CanvasTexture,
  CircleGeometry,
  Color,
  CylinderGeometry,
  DataTexture,
  Group,
  Line,
  LineBasicMaterial,
  Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  MeshToonMaterial,
  NearestFilter,
  PlaneGeometry,
  QuadraticBezierCurve3,
  RedFormat,
  RepeatWrapping,
  SphereGeometry,
  SRGBColorSpace,
  TubeGeometry,
  Vector3,
  type Material,
  type Object3D,
} from "three";
import type { MapBoardLink, MapBoardNode } from "../domain/map-board";
import {
  mapNodeTokenPresentation,
  mapNodeTokenState,
  type MapNodeTokenPresentation,
  type MapNodeTokenState,
} from "./map-node-presentation";

const BOARD_DEPTH = -12;
const PATH_DEPTH = 2;
const NODE_DEPTH = 10;
const TOKEN_TILT = 0.38;
const TOKEN_SEGMENTS = 12;
const PAPER_OVERSCAN = 2_048;

/** Owns one immutable board scene at a fixed logical world size. */
export class AtlasBoardScene {
  readonly root = new Group();
  readonly settlingNodes: Object3D[] = [];
  readonly markersByNodeId = new Map<string, Object3D>();
  readonly #toonRamp = createToonRamp();
  readonly #worldWidth: number;
  readonly #worldHeight: number;

  constructor(
    nodes: readonly MapBoardNode[],
    links: readonly MapBoardLink[],
    worldWidth: number,
    worldHeight: number,
  ) {
    this.#worldWidth = worldWidth;
    this.#worldHeight = worldHeight;
    this.root.add(this.#createPaperPlane(), ...this.#createContourLines());

    const nodesById = new Map(nodes.map((node) => [node.id, node]));
    for (const link of links) {
      const source = nodesById.get(link.source_node_id);
      const target = nodesById.get(link.target_node_id);
      if (source && target)
        this.root.add(this.#createPath(link, source, target));
    }
    for (const node of nodes) {
      const presentation = mapNodeTokenPresentation(node);
      if (!presentation) continue;
      const marker = this.#createNodeMarker(node, presentation);
      this.root.add(marker);
      this.settlingNodes.push(marker);
      this.markersByNodeId.set(node.id, marker);
    }
  }

  detachMarker(nodeId: string): Object3D | undefined {
    const marker = this.markersByNodeId.get(nodeId);
    if (!marker) return undefined;
    this.root.remove(marker);
    this.markersByNodeId.delete(nodeId);
    return marker;
  }

  dispose(): void {
    disposeSceneObject(this.root);
    this.#toonRamp.dispose();
  }

  #createPaperPlane(): Mesh {
    const texture = createPaperTexture();
    const paperWidth = this.#worldWidth + PAPER_OVERSCAN * 2;
    const paperHeight = this.#worldHeight + PAPER_OVERSCAN * 2;
    texture.repeat.set(
      Math.max(2, paperWidth / 280),
      Math.max(2, paperHeight / 240),
    );
    const plane = new Mesh(
      new PlaneGeometry(paperWidth, paperHeight),
      new MeshStandardMaterial({
        color: new Color(palette.paper),
        map: texture,
        roughness: 0.96,
        metalness: 0,
      }),
    );
    plane.position.set(
      this.#worldWidth / 2,
      -this.#worldHeight / 2,
      BOARD_DEPTH,
    );
    return plane;
  }

  #createContourLines(): Line[] {
    const lines: Line[] = [];
    const steps = Math.min(
      128,
      Math.max(16, Math.ceil(this.#worldWidth / 120)),
    );
    for (let row = 0; row < 6; row += 1) {
      const points: Vector3[] = [];
      for (let step = 0; step <= steps; step += 1) {
        const progress = step / steps;
        const x = progress * this.#worldWidth;
        const baseline = ((row + 0.55) / 6) * this.#worldHeight;
        const wave = Math.sin(step * 0.72 + row * 1.4) * 10;
        points.push(new Vector3(x, -(baseline + wave), BOARD_DEPTH + 1));
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
    const distance = Math.max(1, Math.hypot(dx, dy));
    const bend = stableBend(link.id) * Math.min(34, distance * 0.12);
    const control = new Vector3(
      (start.x + end.x) / 2 - (dy / distance) * bend,
      (start.y + end.y) / 2 + (dx / distance) * bend,
      PATH_DEPTH + 3,
    );
    const curve = new QuadraticBezierCurve3(start, control, end);
    const isTrail = link.kind === "trail";
    const isDiscarded =
      link.kind === "discarded" || mapNodeTokenState(target) === "discarded";
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
    const pathRadius = isTrail ? 2.7 : isDiscarded ? 1.2 : 1.7;
    const path = new Mesh(
      new TubeGeometry(curve, 28, pathRadius, 6, false),
      material,
    );
    const bead = new Mesh(
      new SphereGeometry(isTrail ? 5.8 : isDiscarded ? 3 : 4.2, 12, 8),
      material.clone(),
    );
    bead.position.copy(curve.getPoint(0.5));
    const group = new Group();
    if (isTrail) {
      group.add(
        new Mesh(
          new TubeGeometry(curve, 28, pathRadius + 1.1, 6, false),
          new MeshBasicMaterial({
            color: new Color(palette.ink),
            transparent: true,
            opacity: 0.34,
          }),
        ),
      );
    }
    group.add(path, bead);
    return group;
  }

  #createNodeMarker(
    node: MapBoardNode,
    presentation: MapNodeTokenPresentation,
  ): Group {
    const { state, radius } = presentation;
    const isCurrent = state === "current";
    const isDiscarded = state === "discarded";
    const depth = isCurrent ? 18 : 15;
    const group = new Group();
    group.position.copy(this.#pointFor(node, NODE_DEPTH));

    const shadow = new Mesh(
      new CircleGeometry(radius * 1.16, 24),
      new MeshBasicMaterial({
        color: new Color(palette.ink),
        transparent: true,
        opacity: isDiscarded ? 0.08 : 0.2,
      }),
    );
    shadow.position.set(6.5, -8.5, -5.5);
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
        color: new Color(markerColor(state)),
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
    center.position.y = depth / 2 + 0.6;
    token.add(outline, base, center);
    group.add(shadow, token);

    return group;
  }

  #pointFor(node: MapBoardNode, depth: number): Vector3 {
    return new Vector3(
      node.position.x * this.#worldWidth,
      -node.position.y * this.#worldHeight,
      depth + node.position.z * 8,
    );
  }
}

function markerColor(state: MapNodeTokenState): string {
  if (state === "current") return palette.signal;
  if (state === "goal") return palette.ochre;
  if (state === "trail") return palette.moss;
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
  canvas.width = 256;
  canvas.height = 256;
  const context = canvas.getContext("2d");
  if (context) {
    context.fillStyle = palette.paper;
    context.fillRect(0, 0, canvas.width, canvas.height);

    // Broad, low-contrast pulp clouds keep the sheet from reading as flat fill.
    for (let index = 0; index < 18; index += 1) {
      const x = (index * 83 + 29) % canvas.width;
      const y = (index * 47 + 61) % canvas.height;
      const radius = 28 + ((index * 17) % 44);
      const wash = context.createRadialGradient(x, y, 0, x, y, radius);
      wash.addColorStop(
        0,
        colorWithAlpha(
          index % 3 === 0 ? palette.ochre : palette.mutedInk,
          0.018,
        ),
      );
      wash.addColorStop(1, "transparent");
      context.fillStyle = wash;
      context.fillRect(x - radius, y - radius, radius * 2, radius * 2);
    }

    // Directional fibers give the map a lightly pressed, handmade grain.
    context.lineCap = "round";
    for (let index = 0; index < 92; index += 1) {
      const x = (index * 71 + 13) % canvas.width;
      const y = (index * 43 + 7) % canvas.height;
      const length = 10 + ((index * 19) % 52);
      const lift = ((index * 11) % 9) - 4;
      context.beginPath();
      context.moveTo(x, y);
      context.quadraticCurveTo(
        x + length * 0.52,
        y + lift,
        x + length,
        y + lift * 0.35,
      );
      context.strokeStyle = colorWithAlpha(
        index % 11 === 0 ? palette.ochre : palette.mutedInk,
        index % 7 === 0 ? 0.045 : 0.026,
      );
      context.lineWidth = index % 13 === 0 ? 1.15 : 0.55;
      context.stroke();
    }

    // Fine flecks break up the remaining digital smoothness.
    for (let index = 0; index < 560; index += 1) {
      const x = (index * 97 + 17) % canvas.width;
      const y = (index * 151 + 31) % canvas.height;
      const size = index % 37 === 0 ? 1.6 : index % 9 === 0 ? 1 : 0.55;
      context.fillStyle = colorWithAlpha(
        index % 29 === 0 ? palette.ochre : palette.mutedInk,
        index % 13 === 0 ? 0.065 : 0.035,
      );
      context.fillRect(x, y, size, size);
    }
  }
  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace;
  texture.wrapS = RepeatWrapping;
  texture.wrapT = RepeatWrapping;
  return texture;
}

function colorWithAlpha(hex: string, alpha: number): string {
  const value = Number.parseInt(hex.replace("#", ""), 16);
  const red = (value >> 16) & 255;
  const green = (value >> 8) & 255;
  const blue = value & 255;
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

export function disposeSceneObject(object: Object3D): void {
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
