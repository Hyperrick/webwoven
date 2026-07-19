import { AbsoluteFill, Sequence } from "remotion";
import {
  BackgroundMusicTrack,
  type BackgroundMusicTrackProps,
} from "../components/BackgroundMusicTrack";
import { BLACK_FADE_FRAMES, BlackFade } from "../components/BlackFade";
import {
  NarrationTrack,
  type NarrationProps,
} from "../components/NarrationTrack";
import { CloseScene } from "../scenes/CloseScene";
import { CodexScene } from "../scenes/CodexScene";
import { ExplainScene } from "../scenes/ExplainScene";
import { HookScene } from "../scenes/HookScene";
import { IterationScene } from "../scenes/IterationScene";
import { ModesScene } from "../scenes/ModesScene";
import { StartScene } from "../scenes/StartScene";
import { TrustScene } from "../scenes/TrustScene";
import { DEMO_FRAMES, NARRATION_DELAY_FRAMES, scenes } from "../timing";

export type WebwovenDemoProps = NarrationProps & BackgroundMusicTrackProps;

export const WebwovenDemo = ({
  voiceoverFile,
  narrationPlaybackRate,
  musicFile,
  musicVolume,
}: WebwovenDemoProps) => (
  <AbsoluteFill>
    <Sequence
      name="Hook"
      from={scenes.hook.from}
      durationInFrames={scenes.hook.durationInFrames}
    >
      <HookScene durationInFrames={scenes.hook.durationInFrames} />
    </Sequence>
    <Sequence
      name="Start a round"
      from={scenes.start.from}
      durationInFrames={scenes.start.durationInFrames}
    >
      <StartScene durationInFrames={scenes.start.durationInFrames} />
    </Sequence>
    <Sequence
      name="Explainable moves"
      from={scenes.explain.from}
      durationInFrames={scenes.explain.durationInFrames}
    >
      <ExplainScene durationInFrames={scenes.explain.durationInFrames} />
    </Sequence>
    <Sequence
      name="Three modes"
      from={scenes.modes.from}
      durationInFrames={scenes.modes.durationInFrames}
    >
      <ModesScene durationInFrames={scenes.modes.durationInFrames} />
    </Sequence>
    <Sequence
      name="Codex and GPT-5.6"
      from={scenes.codex.from}
      durationInFrames={scenes.codex.durationInFrames}
    >
      <CodexScene durationInFrames={scenes.codex.durationInFrames} />
    </Sequence>
    <Sequence
      name="Iteration"
      from={scenes.iteration.from}
      durationInFrames={scenes.iteration.durationInFrames}
    >
      <IterationScene durationInFrames={scenes.iteration.durationInFrames} />
    </Sequence>
    <Sequence
      name="Trust boundary"
      from={scenes.trust.from}
      durationInFrames={scenes.trust.durationInFrames}
    >
      <TrustScene durationInFrames={scenes.trust.durationInFrames} />
    </Sequence>
    <Sequence name="Close" {...scenes.close}>
      <CloseScene durationInFrames={scenes.close.durationInFrames} />
    </Sequence>
    <Sequence
      name="Opening fade from black"
      durationInFrames={BLACK_FADE_FRAMES + 1}
    >
      <BlackFade direction="in" />
    </Sequence>
    <Sequence
      name="Closing fade to black"
      from={DEMO_FRAMES - BLACK_FADE_FRAMES - 1}
      durationInFrames={BLACK_FADE_FRAMES + 1}
    >
      <BlackFade direction="out" />
    </Sequence>
    <BackgroundMusicTrack musicFile={musicFile} musicVolume={musicVolume} />
    <Sequence name="Narration" from={NARRATION_DELAY_FRAMES}>
      <NarrationTrack
        narrationPlaybackRate={narrationPlaybackRate}
        voiceoverFile={voiceoverFile}
      />
    </Sequence>
  </AbsoluteFill>
);
