import type { MapPoint } from "./map-camera";

const DRAG_THRESHOLD = 6;

export interface MapGestureCallbacks {
  panBy: (delta: MapPoint) => void;
  transformAt: (
    previousAnchor: MapPoint,
    nextAnchor: MapPoint,
    zoomFactor: number,
  ) => void;
  zoomAt: (anchor: MapPoint, zoomFactor: number) => void;
  fitMap: () => void;
  focusCurrent: () => void;
  setPanning: (panning: boolean) => void;
}

interface PointerRecord extends MapPoint {
  startX: number;
  startY: number;
}

export function attachMapGestures(
  viewport: HTMLElement,
  callbacks: MapGestureCallbacks,
): () => void {
  const pointers = new Map<number, PointerRecord>();
  let pinchAnchor: MapPoint | null = null;
  let pinchDistance = 0;
  let dragging = false;
  let spacePressed = false;
  let suppressNextClick = false;
  let clickReleaseTimer: number | undefined;

  const pointFor = (event: PointerEvent | WheelEvent): MapPoint => {
    const bounds = viewport.getBoundingClientRect();
    return { x: event.clientX - bounds.left, y: event.clientY - bounds.top };
  };

  const onPointerDown = (event: PointerEvent): void => {
    const target = event.target;
    const interactive =
      target instanceof Element && target.closest("[data-map-interactive]");
    const canDragAnywhere = event.button === 1 || spacePressed;
    if (interactive && !canDragAnywhere) return;
    if (event.pointerType === "mouse" && event.button > 1) return;
    const point = pointFor(event);
    pointers.set(event.pointerId, {
      ...point,
      startX: point.x,
      startY: point.y,
    });
    viewport.setPointerCapture(event.pointerId);
    if (pointers.size === 2) setPinchAnchor();
  };

  const onPointerMove = (event: PointerEvent): void => {
    const previous = pointers.get(event.pointerId);
    if (!previous) return;
    const next = pointFor(event);
    pointers.set(event.pointerId, {
      ...previous,
      x: next.x,
      y: next.y,
    });

    if (pointers.size >= 2) {
      const pair = [...pointers.values()].slice(0, 2);
      const nextAnchor = midpoint(pair[0], pair[1]);
      const nextDistance = distance(pair[0], pair[1]);
      if (pinchAnchor && pinchDistance > 0)
        callbacks.transformAt(
          pinchAnchor,
          nextAnchor,
          nextDistance / pinchDistance,
        );
      pinchAnchor = nextAnchor;
      pinchDistance = nextDistance;
      startDragging();
      event.preventDefault();
      return;
    }

    const moved = Math.hypot(
      next.x - previous.startX,
      next.y - previous.startY,
    );
    if (!dragging && moved < DRAG_THRESHOLD) return;
    if (!dragging) {
      callbacks.panBy({
        x: next.x - previous.startX,
        y: next.y - previous.startY,
      });
      startDragging();
    } else {
      callbacks.panBy({ x: next.x - previous.x, y: next.y - previous.y });
    }
    event.preventDefault();
  };

  const releasePointer = (event: PointerEvent): void => {
    pointers.delete(event.pointerId);
    if (viewport.hasPointerCapture(event.pointerId))
      viewport.releasePointerCapture(event.pointerId);
    if (pointers.size === 1) {
      const remaining = [...pointers.values()][0];
      remaining.startX = remaining.x;
      remaining.startY = remaining.y;
    }
    if (pointers.size < 2) {
      pinchAnchor = null;
      pinchDistance = 0;
    }
    if (pointers.size === 0 && dragging) {
      dragging = false;
      suppressNextClick = true;
      window.clearTimeout(clickReleaseTimer);
      clickReleaseTimer = window.setTimeout(() => {
        suppressNextClick = false;
      }, 120);
      callbacks.setPanning(false);
    }
  };

  const onWheel = (event: WheelEvent): void => {
    const target = event.target;
    if (target instanceof Element && target.closest("[data-map-scrollable]"))
      return;
    event.preventDefault();
    const factor = Math.min(
      1.25,
      Math.max(0.8, Math.exp(-event.deltaY * 0.0015)),
    );
    callbacks.zoomAt(pointFor(event), factor);
  };

  const onKeyDown = (event: KeyboardEvent): void => {
    const target = event.target;
    if (target instanceof Element && target.closest("[data-map-interactive]"))
      return;
    if (event.key === " ") {
      spacePressed = true;
      event.preventDefault();
      return;
    }
    const panStep = 64;
    if (event.key === "ArrowLeft") callbacks.panBy({ x: panStep, y: 0 });
    else if (event.key === "ArrowRight") callbacks.panBy({ x: -panStep, y: 0 });
    else if (event.key === "ArrowUp") callbacks.panBy({ x: 0, y: panStep });
    else if (event.key === "ArrowDown") callbacks.panBy({ x: 0, y: -panStep });
    else if (event.key === "+" || event.key === "=")
      callbacks.zoomAt(viewportCenter(viewport), 1.2);
    else if (event.key === "-" || event.key === "_")
      callbacks.zoomAt(viewportCenter(viewport), 1 / 1.2);
    else if (event.key === "0") callbacks.fitMap();
    else if (event.key === "Home") callbacks.focusCurrent();
    else return;
    event.preventDefault();
  };

  const onKeyUp = (event: KeyboardEvent): void => {
    if (event.key === " ") spacePressed = false;
  };

  const onClickCapture = (event: MouseEvent): void => {
    if (!suppressNextClick) return;
    suppressNextClick = false;
    window.clearTimeout(clickReleaseTimer);
    event.preventDefault();
    event.stopPropagation();
  };

  function setPinchAnchor(): void {
    const pair = [...pointers.values()].slice(0, 2);
    pinchAnchor = midpoint(pair[0], pair[1]);
    pinchDistance = distance(pair[0], pair[1]);
  }

  function startDragging(): void {
    if (dragging) return;
    dragging = true;
    callbacks.setPanning(true);
  }

  viewport.addEventListener("pointerdown", onPointerDown);
  viewport.addEventListener("pointermove", onPointerMove);
  viewport.addEventListener("pointerup", releasePointer);
  viewport.addEventListener("pointercancel", releasePointer);
  viewport.addEventListener("wheel", onWheel, { passive: false });
  viewport.addEventListener("keydown", onKeyDown);
  viewport.addEventListener("keyup", onKeyUp);
  viewport.addEventListener("click", onClickCapture, true);

  return () => {
    window.clearTimeout(clickReleaseTimer);
    viewport.removeEventListener("pointerdown", onPointerDown);
    viewport.removeEventListener("pointermove", onPointerMove);
    viewport.removeEventListener("pointerup", releasePointer);
    viewport.removeEventListener("pointercancel", releasePointer);
    viewport.removeEventListener("wheel", onWheel);
    viewport.removeEventListener("keydown", onKeyDown);
    viewport.removeEventListener("keyup", onKeyUp);
    viewport.removeEventListener("click", onClickCapture, true);
  };
}

function midpoint(left: MapPoint, right: MapPoint): MapPoint {
  return { x: (left.x + right.x) / 2, y: (left.y + right.y) / 2 };
}

function distance(left: MapPoint, right: MapPoint): number {
  return Math.hypot(right.x - left.x, right.y - left.y);
}

function viewportCenter(viewport: HTMLElement): MapPoint {
  return { x: viewport.clientWidth / 2, y: viewport.clientHeight / 2 };
}
