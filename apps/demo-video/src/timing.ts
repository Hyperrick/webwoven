export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;
export const SCENE_TRANSITION_FRAMES = 12;

export const seconds = (value: number) => Math.round(value * FPS);

export const scenes = {
  hook: { from: seconds(0), durationInFrames: seconds(11.3) },
  start: { from: seconds(11.3), durationInFrames: seconds(15.1) },
  explain: { from: seconds(26.4), durationInFrames: seconds(23.7) },
  modes: { from: seconds(50.1), durationInFrames: seconds(16.4) },
  codex: { from: seconds(66.5), durationInFrames: seconds(28.8) },
  iteration: { from: seconds(95.3), durationInFrames: seconds(21.9) },
  trust: { from: seconds(117.2), durationInFrames: seconds(20.9) },
  close: { from: seconds(138.1), durationInFrames: seconds(12.9) },
} as const;

export const DEMO_FRAMES = seconds(151);
export const TEASER_FRAMES = seconds(24);
