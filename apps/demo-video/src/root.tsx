import { Composition } from "remotion";
import { WebwovenDemo } from "./compositions/WebwovenDemo";
import { WebwovenTeaser } from "./compositions/WebwovenTeaser";
import { DEMO_FRAMES, FPS, HEIGHT, TEASER_FRAMES, WIDTH } from "./timing";

export const VideoRoot = () => (
  <>
    <Composition
      id="WebwovenDemo"
      component={WebwovenDemo}
      durationInFrames={DEMO_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      defaultProps={{ voiceoverFile: "" }}
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
