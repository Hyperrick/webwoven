export interface LandingRouteMapPoint {
  x: number;
  y: number;
}

export interface LandingRouteMapContour extends LandingRouteMapPoint {
  radiusX: number;
  radiusY: number;
}

export interface LandingRouteMapLayout {
  points: LandingRouteMapPoint[];
  verticalFolds: number[];
  horizontalFolds: number[];
  contours: LandingRouteMapContour[];
}

function hashSeed(seed: string): number {
  let hash = 0x811c9dc5;
  for (let index = 0; index < seed.length; index += 1) {
    hash ^= seed.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return hash >>> 0;
}

function seededRandom(seed: string): () => number {
  let state = hashSeed(seed);
  return () => {
    state += 0x6d2b79f5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4_294_967_296;
  };
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}

function between(
  random: () => number,
  minimum: number,
  maximum: number,
): number {
  return minimum + random() * (maximum - minimum);
}

/**
 * Creates stable decorative map geometry for a route preview. The coordinates
 * are atlas grid references, not geographic positions.
 */
export function createLandingRouteMapLayout(
  seed: string,
  pointCount: number,
): LandingRouteMapLayout {
  if (!Number.isInteger(pointCount) || pointCount < 2) {
    throw new RangeError("A landing route map needs at least two points.");
  }

  const random = seededRandom(seed);
  const start = {
    x: round(between(random, 12, 16)),
    y: round(between(random, 14, 19)),
  };
  const goal = {
    x: round(between(random, 84, 88)),
    y: round(between(random, 77, 83)),
  };
  const points = [start];

  for (let index = 1; index < pointCount - 1; index += 1) {
    const progress = index / (pointCount - 1);
    const wave = index % 2 === 0 ? 4 : -4;
    points.push({
      x: round(
        start.x + (goal.x - start.x) * progress + between(random, -2.5, 2.5),
      ),
      y: round(
        clamp(
          start.y +
            (goal.y - start.y) * progress +
            wave +
            between(random, -4, 4),
          23,
          73,
        ),
      ),
    });
  }
  points.push(goal);

  return {
    points,
    verticalFolds: [
      round(between(random, 31, 38)),
      round(between(random, 65, 73)),
    ],
    horizontalFolds: [round(between(random, 45, 57))],
    contours: [
      {
        x: round(between(random, 16, 25)),
        y: round(between(random, 61, 72)),
        radiusX: round(between(random, 5, 8)),
        radiusY: round(between(random, 3, 5)),
      },
      {
        x: round(between(random, 67, 77)),
        y: round(between(random, 18, 29)),
        radiusX: round(between(random, 6, 9)),
        radiusY: round(between(random, 3, 5)),
      },
      {
        x: round(between(random, 72, 83)),
        y: round(between(random, 59, 70)),
        radiusX: round(between(random, 5, 8)),
        radiusY: round(between(random, 3, 5)),
      },
    ],
  };
}
