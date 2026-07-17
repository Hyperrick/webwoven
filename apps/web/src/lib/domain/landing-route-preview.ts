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
    number: "0138",
    start: "Claude Monet",
    target: "Spirited Away",
    moves: 4,
    categoryPath: "Art & Design → Film & Media",
  },
  {
    number: "0274",
    start: "The Godfather",
    target: "Earth",
    moves: 4,
    categoryPath: "Film & Media → Nature & Life",
  },
  {
    number: "0359",
    start: "United Nations",
    target: "telescope",
    moves: 4,
    categoryPath: "History & Society → Science & Technology",
  },
  {
    number: "0416",
    start: "George Orwell",
    target: "Beyoncé",
    moves: 4,
    categoryPath: "Literature & Language → Music & Performance",
  },
  {
    number: "0528",
    start: "Bob Dylan",
    target: "Serena Williams",
    moves: 4,
    categoryPath: "Music & Performance → Sports & Games",
  },
  {
    number: "0643",
    start: "galaxy",
    target: "Black Death",
    moves: 4,
    categoryPath: "Nature & Life → History & Society",
  },
  {
    number: "0712",
    start: "Napoleon",
    target: "Claude Monet",
    moves: 4,
    categoryPath: "People → Art & Design",
  },
  {
    number: "0837",
    start: "Guggenheim Museum Bilbao",
    target: "Nelson Mandela",
    moves: 4,
    categoryPath: "Places & Architecture → People",
  },
  {
    number: "0924",
    start: "Alan Turing",
    target: "Spirited Away",
    moves: 4,
    categoryPath: "Science & Technology → Film & Media",
  },
  {
    number: "1066",
    start: "Lionel Messi",
    target: "George Orwell",
    moves: 4,
    categoryPath: "Sports & Games → Literature & Language",
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
