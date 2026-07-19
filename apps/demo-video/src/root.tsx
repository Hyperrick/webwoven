import { Composition } from "remotion";
import { WebwovenDemo } from "./compositions/WebwovenDemo";
import { WebwovenTeaser } from "./compositions/WebwovenTeaser";
import {
  DEMO_FRAMES,
  FPS,
  HEIGHT,
  NARRATION_PLAYBACK_RATE,
  TEASER_FRAMES,
  WIDTH,
} from "./timing";

export const VideoRoot = () => (
  <>
    <Composition
      id="WebwovenDemo"
      component={WebwovenDemo}
      durationInFrames={DEMO_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      defaultProps={{
        musicFile: "",
        musicVolume: 0.055,
        narrationPlaybackRate: NARRATION_PLAYBACK_RATE,
        voiceoverFile: "",
      }}
    />
    <Composition
      id="WebwovenTeaser"
      component={WebwovenTeaser}
      durationInFrames={TEASER_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  </>
);
