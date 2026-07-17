import type { Category, Difficulty, GameMode, HintType } from "../api/types";

export interface AnalyticsConfig {
  origin: string;
  websiteId: string;
  domain: string;
}

type MovesRelativeToPar = "under_par" | "at_par" | "over_par" | "unknown";
type HintCount = "none" | "one" | "multiple";
type RouteProgress = "no_moves" | "in_progress";

interface AnalyticsEvents {
  mode_selected: { mode: GameMode };
  round_started: {
    mode: GameMode;
    difficulty: Difficulty;
    category: Category;
  };
  round_completed: {
    mode: GameMode;
    difficulty: Difficulty;
    category: Category;
    result: "goal_reached";
    moves_relative_to_par: MovesRelativeToPar;
    hints: HintCount;
  };
  hint_used: {
    mode: GameMode;
    difficulty: Difficulty;
    category: Category;
    hint: HintType;
  };
  route_abandoned: {
    mode: GameMode;
    difficulty: Difficulty;
    category: Category;
    progress: RouteProgress;
  };
}

type AnalyticsEventName = keyof AnalyticsEvents;
type AnalyticsValue = string | number | boolean;
type UmamiTracker = {
  track(name: string, data: Record<string, AnalyticsValue>): void;
};

const EVENT_FIELDS: {
  [Name in AnalyticsEventName]: readonly (keyof AnalyticsEvents[Name])[];
} = {
  mode_selected: ["mode"],
  round_started: ["mode", "difficulty", "category"],
  round_completed: [
    "mode",
    "difficulty",
    "category",
    "result",
    "moves_relative_to_par",
    "hints",
  ],
  hint_used: ["mode", "difficulty", "category", "hint"],
  route_abandoned: ["mode", "difficulty", "category", "progress"],
};

const MAX_PENDING_EVENTS = 20;
const pendingEvents: Array<{
  name: AnalyticsEventName;
  data: Record<string, AnalyticsValue>;
}> = [];

declare global {
  interface Window {
    umami?: UmamiTracker;
  }
}

export function analyticsConfigFromEnvironment(): AnalyticsConfig | null {
  const origin = import.meta.env.VITE_ANALYTICS_ORIGIN?.trim();
  const websiteId = import.meta.env.VITE_ANALYTICS_WEBSITE_ID?.trim();
  const domain = import.meta.env.VITE_ANALYTICS_DOMAIN?.trim();
  if (!origin || !websiteId || !domain) return null;
  return { origin, websiteId, domain };
}

export function analyticsAllowed(
  doNotTrack: string | null | undefined,
): boolean {
  return doNotTrack !== "1" && doNotTrack?.toLowerCase() !== "yes";
}

export function analyticsScriptAttributes(
  config: AnalyticsConfig,
): Record<string, string> {
  return {
    src: `${config.origin.replace(/\/$/, "")}/script.js`,
    "data-host-url": config.origin.replace(/\/$/, ""),
    "data-website-id": config.websiteId,
    "data-domains": config.domain,
    "data-do-not-track": "true",
    "data-exclude-search": "true",
    "data-exclude-hash": "true",
  };
}

export function initializeAnalytics(
  config: AnalyticsConfig | null = analyticsConfigFromEnvironment(),
): boolean {
  if (
    !config ||
    typeof document === "undefined" ||
    typeof navigator === "undefined" ||
    !analyticsAllowed(navigator.doNotTrack) ||
    document.getElementById("webwoven-analytics")
  ) {
    return false;
  }

  const script = document.createElement("script");
  script.id = "webwoven-analytics";
  script.defer = true;
  for (const [name, value] of Object.entries(
    analyticsScriptAttributes(config),
  )) {
    script.setAttribute(name, value);
  }
  script.addEventListener("load", flushPendingEvents, { once: true });
  document.head.append(script);
  return true;
}

export function trackAnalytics<Name extends AnalyticsEventName>(
  name: Name,
  data: AnalyticsEvents[Name],
): boolean {
  if (
    typeof navigator !== "undefined" &&
    !analyticsAllowed(navigator.doNotTrack)
  ) {
    return false;
  }
  const sanitized = sanitizeAnalyticsEvent(name, data);
  const tracker = typeof window === "undefined" ? undefined : window.umami;
  if (!tracker) {
    if (pendingEvents.length < MAX_PENDING_EVENTS) {
      pendingEvents.push({ name, data: sanitized });
    }
    return false;
  }
  tracker.track(name, sanitized);
  return true;
}

export function sanitizeAnalyticsEvent<Name extends AnalyticsEventName>(
  name: Name,
  data: AnalyticsEvents[Name],
): Record<string, AnalyticsValue> {
  const sanitized: Record<string, AnalyticsValue> = {};
  for (const field of EVENT_FIELDS[name]) {
    const value = data[field];
    if (
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean"
    ) {
      sanitized[String(field)] = value;
    }
  }
  return sanitized;
}

export function movesRelativeToPar(
  moves: number,
  par: number | null,
): MovesRelativeToPar {
  if (par === null) return "unknown";
  if (moves < par) return "under_par";
  if (moves === par) return "at_par";
  return "over_par";
}

export function hintCount(count: number): HintCount {
  if (count === 0) return "none";
  if (count === 1) return "one";
  return "multiple";
}

function flushPendingEvents(): void {
  if (typeof window === "undefined" || !window.umami) return;
  for (const event of pendingEvents.splice(0)) {
    window.umami.track(event.name, event.data);
  }
}
