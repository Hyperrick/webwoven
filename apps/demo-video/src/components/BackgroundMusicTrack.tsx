import { Audio } from "@remotion/media";
import { interpolate, staticFile } from "remotion";

import { DEMO_FRAMES, FPS } from "../timing";

export type BackgroundMusicTrackProps = {
  musicFile?: string;
  musicVolume?: number;
};

const FADE_IN_FRAMES = 2 * FPS;
const FADE_OUT_FRAMES = 3 * FPS;

export const BackgroundMusicTrack = ({
  musicFile,
  musicVolume = 0.055,
}: BackgroundMusicTrackProps) => {
  if (!musicFile || musicVolume <= 0) {
    return null;
  }

  const peakVolume = Math.min(musicVolume, 1);

  return (
    <Audio
      loop
      loopVolumeCurveBehavior="extend"
      src={staticFile(musicFile)}
      volume={(frame) =>
        interpolate(
          frame,
          [0, FADE_IN_FRAMES, DEMO_FRAMES - FADE_OUT_FRAMES, DEMO_FRAMES],
          [0, peakVolume, peakVolume, 0],
          {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          },
        )
      }
    />
  );
};
