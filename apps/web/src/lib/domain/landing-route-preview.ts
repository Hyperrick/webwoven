interface LandingRouteSample {
  number: string;
  start: string;
  target: string;
  moves: number;
  categoryPath: string;
}

export interface LandingRouteStep {
  number: string;
  label: string;
  hidden: boolean;
}

export interface LandingRoutePreview extends LandingRouteSample {
  steps: LandingRouteStep[];
}

const ROUTE_SAMPLES: readonly LandingRouteSample[] = [
  {
    number: "0042",
    start: "Hokusai",
    target: "United Kingdom",
    moves: 4,
    categoryPath: "Art & Design → Places & Architecture",
  },
  {
    number: "0187",
    start: "Hokusai",
    target: "England",
    moves: 4,
    categoryPath: "Art & Design → Places & Architecture",
  },
  {
    number: "0264",
    start: "Mount Fuji",
    target: "British Museum",
    moves: 4,
    categoryPath: "Nature & Life → Art & Design",
  },
  {
    number: "0731",
    start: "Thirty-six Views of Mount Fuji",
    target: "London",
    moves: 4,
    categoryPath: "Art & Design → Places & Architecture",
  },
] as const;

function stepNumber(index: number): string {
  return String(index + 1).padStart(2, "0");
}

export function createLandingRoutePreview(
  random: () => number = Math.random,
): LandingRoutePreview {
  const sampleIndex = Math.min(
    ROUTE_SAMPLES.length - 1,
    Math.max(0, Math.floor(random() * ROUTE_SAMPLES.length)),
  );
  const sample = ROUTE_SAMPLES[sampleIndex];
  const steps = Array.from({ length: sample.moves + 1 }, (_, index) => ({
    number: stepNumber(index),
    label:
      index === 0 ? sample.start : index === sample.moves ? sample.target : "…",
    hidden: index > 0 && index < sample.moves,
  }));

  return { ...sample, steps };
}
