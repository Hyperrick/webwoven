export interface Preferences {
  reducedMotion: boolean;
  highContrast: boolean;
  sound: boolean;
}

export const DEFAULT_PREFERENCES: Preferences = {
  reducedMotion: false,
  highContrast: false,
  sound: true,
};

const STORAGE_KEY = "webwoven.preferences";

export function loadPreferences(): Preferences {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value
      ? {
          ...DEFAULT_PREFERENCES,
          ...(JSON.parse(value) as Partial<Preferences>),
        }
      : DEFAULT_PREFERENCES;
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function persistPreferences(preferences: Preferences): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
  document.documentElement.dataset.motion = preferences.reducedMotion
    ? "reduced"
    : "full";
  document.documentElement.dataset.contrast = preferences.highContrast
    ? "high"
    : "standard";
}
