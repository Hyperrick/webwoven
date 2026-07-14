import { palette } from "@webwoven/design-tokens/tokens";
import {
  AmbientLight,
  BufferGeometry,
  Color,
  DirectionalLight,
  DoubleSide,
  Group,
  Line,
  LineBasicMaterial,
  Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  OrthographicCamera,
  PlaneGeometry,
  QuadraticBezierCurve3,
  Scene,
  ShaderMaterial,
  SphereGeometry,
  SRGBColorSpace,
  Texture,
  TextureLoader,
  TubeGeometry,
  Vector3,
  WebGLRenderer,
  type Material,
  type Object3D,
} from "three";
import type { RoundIntroTimeline } from "./timeline";

interface SceneOptions {
  artwork: string;
  accent: string;
  startImage?: string;
  targetImage?: string;
  onUnavailable: () => void;
}

const VIEW_HEIGHT = 8;

export class RoundIntroScene {
  readonly #scene = new Scene();
  readonly #camera = new OrthographicCamera();
  readonly #renderer: WebGLRenderer;
  readonly #categorySheet = new Group();
  readonly #endpointGroup = new Group();
  readonly #startCard: Group;
  readonly #goalCard: Group;
  readonly #route: Mesh;
  readonly #particles = new Group();
  readonly #grain: Mesh<PlaneGeometry, ShaderMaterial>;
  readonly #observer: ResizeObserver;
  readonly #onContextLost: (event: Event) => void;
  readonly #textures = new Set<Texture>();
  #disposed = false;

  constructor(host: HTMLElement, options: SceneOptions) {
    this.#renderer = new WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: "low-power",
    });
    this.#renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    this.#renderer.outputColorSpace = SRGBColorSpace;
    this.#renderer.setClearAlpha(0);
    this.#renderer.domElement.setAttribute("aria-hidden", "true");
    this.#onContextLost = (event) => {
      event.preventDefault();
      options.onUnavailable();
    };
    this.#renderer.domElement.addEventListener(
      "webglcontextlost",
      this.#onContextLost,
    );
    host.append(this.#renderer.domElement);

    this.#camera.position.set(0, 0, 10);
    this.#camera.lookAt(0, 0, 0);
    this.#scene.add(new AmbientLight(new Color(palette.paper), 1.8));
    const key = new DirectionalLight(new Color(palette.paper), 3.4);
    key.position.set(-4, 6, 8);
    this.#scene.add(key);

    this.#categorySheet.add(this.#paperPlane(5.6, 3.8, 0.97));
    this.#categorySheet.add(this.#artPlane(options.artwork, 5.05, 3.25, 0.03));
    this.#categorySheet.add(...registrationMarks(5.85, 4.05));
    this.#scene.add(this.#categorySheet);

    this.#startCard = this.#card(options.startImage, options.accent);
    this.#goalCard = this.#card(options.targetImage, palette.ochre);
    this.#startCard.position.x = -2.55;
    this.#goalCard.position.x = 2.55;
    this.#endpointGroup.add(this.#startCard, this.#goalCard);
    const curve = new QuadraticBezierCurve3(
      new Vector3(-1.55, 0, -0.05),
      new Vector3(0, 1.15, 0.1),
      new Vector3(1.55, 0, -0.05),
    );
    this.#route = new Mesh(
      new TubeGeometry(curve, 44, 0.035, 6, false),
      new MeshBasicMaterial({ color: new Color(options.accent) }),
    );
    this.#endpointGroup.add(this.#route);
    this.#scene.add(this.#endpointGroup);

    for (let index = 0; index < 34; index += 1) {
      const particle = new Mesh(
        new SphereGeometry(index % 5 === 0 ? 0.025 : 0.012, 6, 4),
        new MeshBasicMaterial({
          color: new Color(index % 3 === 0 ? options.accent : palette.mutedInk),
          transparent: true,
          opacity: 0.28,
        }),
      );
      particle.position.set(
        ((index * 37) % 100) / 8 - 6.25,
        ((index * 61) % 100) / 14 - 3.55,
        -0.4,
      );
      this.#particles.add(particle);
    }
    this.#scene.add(this.#particles);

    this.#grain = new Mesh(
      new PlaneGeometry(16, 10),
      new ShaderMaterial({
        transparent: true,
        depthWrite: false,
        uniforms: {
          uTime: { value: 0 },
          uDissolve: { value: 0 },
          uAccent: { value: new Color(options.accent) },
        },
        vertexShader:
          "varying vec2 vUv; void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}",
        fragmentShader:
          "varying vec2 vUv; uniform float uTime; uniform float uDissolve; uniform vec3 uAccent; void main(){float n=fract(sin(dot(vUv*997.0+uTime,vec2(12.9898,78.233)))*43758.5453);if(n<uDissolve*0.16)discard;float a=n>0.92?0.055:0.012;gl_FragColor=vec4(uAccent,a);}",
      }),
    );
    this.#grain.position.z = 1;
    this.#scene.add(this.#grain);

    this.#observer = new ResizeObserver(() => this.#resize(host));
    this.#observer.observe(host);
    this.#resize(host);
  }

  update(timeline: RoundIntroTimeline): void {
    if (this.#disposed) return;
    const category = ease(timeline.category);
    const endpoints = ease(timeline.endpoints);
    const categoryExit = Math.min(1, timeline.endpoints * 4);
    const orientation = ease(timeline.orientation);
    const launch = ease(timeline.launch);

    this.#categorySheet.position.y = (1 - category) * 0.45 + endpoints * 0.65;
    this.#categorySheet.rotation.z = (1 - category) * -0.045;
    this.#categorySheet.scale.setScalar(
      0.82 + category * 0.18 - endpoints * 0.12,
    );
    setOpacity(this.#categorySheet, 1 - categoryExit);

    this.#endpointGroup.visible = timeline.elapsed_ms >= 1_100;
    this.#endpointGroup.scale.setScalar(0.78 + endpoints * 0.22);
    setOpacity(this.#endpointGroup, endpoints);
    this.#startCard.position.x = -0.7 - endpoints * 1.85;
    this.#goalCard.position.x = 0.7 + endpoints * 1.85;
    this.#route.scale.x = Math.max(0.001, endpoints);

    this.#camera.position.x = orientation * -2.45;
    this.#camera.zoom = 1 + orientation * 0.14 + launch * 1.7;
    this.#camera.updateProjectionMatrix();
    this.#goalCard.position.y = orientation * -0.25;
    this.#startCard.scale.setScalar(1 + launch * 2.2);
    this.#startCard.position.x += launch * 2.45;
    this.#goalCard.scale.setScalar(1 - launch * 0.35);
    setOpacity(this.#goalCard, 1 - launch);
    setOpacity(this.#route, 1 - launch);

    this.#particles.rotation.z = timeline.overall * 0.035;
    this.#grain.material.uniforms.uTime.value = timeline.elapsed_ms / 1_000;
    this.#grain.material.uniforms.uDissolve.value = launch;
    this.#renderer.render(this.#scene, this.#camera);
  }

  dispose(): void {
    if (this.#disposed) return;
    this.#disposed = true;
    this.#observer.disconnect();
    this.#renderer.domElement.removeEventListener(
      "webglcontextlost",
      this.#onContextLost,
    );
    disposeObject(this.#scene);
    this.#textures.forEach((texture) => texture.dispose());
    this.#renderer.dispose();
    this.#renderer.domElement.remove();
  }

  #card(image: string | undefined, accent: string): Group {
    const group = new Group();
    group.add(this.#paperPlane(3.05, 2.1, 0.98));
    if (image) group.add(this.#artPlane(image, 2.72, 1.76, 0.04));
    const rule = new Mesh(
      new PlaneGeometry(3.05, 0.08),
      new MeshBasicMaterial({ color: new Color(accent) }),
    );
    rule.position.set(0, -1.01, 0.08);
    group.add(rule);
    return group;
  }

  #paperPlane(width: number, height: number, opacity: number): Mesh {
    return new Mesh(
      new PlaneGeometry(width, height),
      new MeshStandardMaterial({
        color: new Color(palette.paper),
        roughness: 0.96,
        metalness: 0,
        transparent: true,
        opacity,
        side: DoubleSide,
      }),
    );
  }

  #artPlane(path: string, width: number, height: number, z: number): Mesh {
    const material = new MeshBasicMaterial({
      color: new Color(palette.paper),
      transparent: true,
      opacity: 0.98,
    });
    const plane = new Mesh(new PlaneGeometry(width, height), material);
    plane.position.z = z;
    new TextureLoader().load(path, (texture) => {
      if (this.#disposed) {
        texture.dispose();
        return;
      }
      texture.colorSpace = SRGBColorSpace;
      this.#textures.add(texture);
      material.map = texture;
      material.color.set(0xffffff);
      material.needsUpdate = true;
    });
    return plane;
  }

  #resize(host: HTMLElement): void {
    const width = Math.max(1, host.clientWidth);
    const height = Math.max(1, host.clientHeight);
    const aspect = width / height;
    this.#camera.left = (-VIEW_HEIGHT * aspect) / 2;
    this.#camera.right = (VIEW_HEIGHT * aspect) / 2;
    this.#camera.top = VIEW_HEIGHT / 2;
    this.#camera.bottom = -VIEW_HEIGHT / 2;
    this.#camera.near = 0.1;
    this.#camera.far = 30;
    this.#camera.updateProjectionMatrix();
    this.#renderer.setSize(width, height, false);
  }
}

function registrationMarks(width: number, height: number): Line[] {
  return [
    [
      [-width / 2, height / 2],
      [-width / 2 + 0.38, height / 2],
    ],
    [
      [width / 2, -height / 2],
      [width / 2 - 0.38, -height / 2],
    ],
  ].map(
    (points) =>
      new Line(
        new BufferGeometry().setFromPoints(
          points.map(([x, y]) => new Vector3(x, y, 0.1)),
        ),
        new LineBasicMaterial({ color: new Color(palette.ink) }),
      ),
  );
}

function setOpacity(object: Object3D, opacity: number): void {
  object.traverse((child) => {
    if (!(child instanceof Mesh) && !(child instanceof Line)) return;
    const materials = Array.isArray(child.material)
      ? child.material
      : [child.material];
    for (const material of materials) {
      if (material instanceof ShaderMaterial) continue;
      const base = (material.userData.baseOpacity ??
        material.opacity) as number;
      material.userData.baseOpacity = base;
      material.transparent = true;
      material.opacity = base * Math.max(0, Math.min(1, opacity));
    }
  });
}

function disposeObject(object: Object3D): void {
  const geometries = new Set<BufferGeometry>();
  const materials = new Set<Material>();
  object.traverse((child) => {
    if (!(child instanceof Mesh) && !(child instanceof Line)) return;
    geometries.add(child.geometry);
    (Array.isArray(child.material) ? child.material : [child.material]).forEach(
      (material) => materials.add(material),
    );
  });
  geometries.forEach((geometry) => geometry.dispose());
  materials.forEach((material) => material.dispose());
  object.clear();
}

function ease(value: number): number {
  return 1 - (1 - value) ** 3;
}
