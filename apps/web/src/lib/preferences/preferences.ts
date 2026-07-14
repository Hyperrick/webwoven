export interface Preferences {
  reducedMotion: boolean;
  sound: boolean;
}

export const DEFAULT_PREFERENCES: Preferences = {
  reducedMotion: false,
  sound: true,
};

const STORAGE_KEY = "webwoven.preferences";

export function loadPreferences(): Preferences {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    if (!value) return DEFAULT_PREFERENCES;
    const stored = JSON.parse(value) as Partial<Preferences>;
    return {
      reducedMotion:
        typeof stored.reducedMotion === "boolean"
          ? stored.reducedMotion
          : DEFAULT_PREFERENCES.reducedMotion,
      sound:
        typeof stored.sound === "boolean"
          ? stored.sound
          : DEFAULT_PREFERENCES.sound,
    };
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function persistPreferences(preferences: Preferences): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
  document.documentElement.dataset.motion = preferences.reducedMotion
    ? "reduced"
    : "full";
}

/** Combines the in-app choice with the operating-system motion preference. */
export function shouldReduceMotion(
  appRequestsReduction = document.documentElement.dataset.motion === "reduced",
  systemRequestsReduction = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches,
): boolean {
  return appRequestsReduction || systemRequestsReduction;
}
