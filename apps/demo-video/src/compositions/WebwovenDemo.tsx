import { AbsoluteFill, Sequence } from "remotion";
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
import { scenes, SCENE_TRANSITION_FRAMES } from "../timing";

const withExitOverlap = (durationInFrames: number) =>
  durationInFrames + SCENE_TRANSITION_FRAMES;

export const WebwovenDemo = ({ voiceoverFile }: NarrationProps) => (
  <AbsoluteFill>
    <Sequence
      name="Hook"
      from={scenes.hook.from}
      durationInFrames={withExitOverlap(scenes.hook.durationInFrames)}
    >
      <HookScene durationInFrames={scenes.hook.durationInFrames} />
    </Sequence>
    <Sequence
      name="Start a round"
      from={scenes.start.from}
      durationInFrames={withExitOverlap(scenes.start.durationInFrames)}
    >
      <StartScene durationInFrames={scenes.start.durationInFrames} />
    </Sequence>
    <Sequence
      name="Explainable moves"
      from={scenes.explain.from}
      durationInFrames={withExitOverlap(scenes.explain.durationInFrames)}
    >
      <ExplainScene durationInFrames={scenes.explain.durationInFrames} />
    </Sequence>
    <Sequence
      name="Three modes"
      from={scenes.modes.from}
      durationInFrames={withExitOverlap(scenes.modes.durationInFrames)}
    >
      <ModesScene durationInFrames={scenes.modes.durationInFrames} />
    </Sequence>
    <Sequence
      name="Codex and GPT-5.6"
      from={scenes.codex.from}
      durationInFrames={withExitOverlap(scenes.codex.durationInFrames)}
    >
      <CodexScene durationInFrames={scenes.codex.durationInFrames} />
    </Sequence>
    <Sequence
      name="Iteration"
      from={scenes.iteration.from}
      durationInFrames={withExitOverlap(scenes.iteration.durationInFrames)}
    >
      <IterationScene durationInFrames={scenes.iteration.durationInFrames} />
    </Sequence>
    <Sequence
      name="Trust boundary"
      from={scenes.trust.from}
      durationInFrames={withExitOverlap(scenes.trust.durationInFrames)}
    >
      <TrustScene durationInFrames={scenes.trust.durationInFrames} />
    </Sequence>
    <Sequence name="Close" {...scenes.close}>
      <CloseScene durationInFrames={scenes.close.durationInFrames} />
    </Sequence>
    <NarrationTrack voiceoverFile={voiceoverFile} />
  </AbsoluteFill>
);
