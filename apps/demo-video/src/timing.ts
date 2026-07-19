export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;
export const SCENE_TRANSITION_FRAMES = 12;
export const NARRATION_PLAYBACK_RATE = 1.09;
export const NARRATION_DELAY_FRAMES = FPS;

export const seconds = (value: number) => Math.round(value * FPS);

export const scenes = {
  hook: { from: seconds(0), durationInFrames: seconds(12) },
  start: { from: seconds(12), durationInFrames: seconds(16.7) },
  explain: { from: seconds(28.7), durationInFrames: seconds(26.7) },
  modes: { from: seconds(55.4), durationInFrames: seconds(20.5) },
  codex: { from: seconds(75.9), durationInFrames: seconds(30.9) },
  iteration: { from: seconds(106.8), durationInFrames: seconds(26.7) },
  trust: { from: seconds(133.5), durationInFrames: seconds(30.3) },
  close: { from: seconds(163.8), durationInFrames: seconds(14.2) },
} as const;

export const DEMO_FRAMES = seconds(178);
export const TEASER_FRAMES = seconds(24);
