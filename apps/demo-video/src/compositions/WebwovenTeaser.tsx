import { AbsoluteFill, Sequence } from "remotion";
import { CloseScene } from "../scenes/CloseScene";
import { GameplayScene } from "../scenes/GameplayScene";
import { HookScene } from "../scenes/HookScene";
import { SCENE_TRANSITION_FRAMES, seconds } from "../timing";

const teaser = {
  hook: { from: seconds(0), durationInFrames: seconds(7) },
  gameplay: { from: seconds(7), durationInFrames: seconds(12) },
  close: { from: seconds(19), durationInFrames: seconds(5) },
} as const;

export const WebwovenTeaser = () => (
  <AbsoluteFill>
    <Sequence
      name="Hook"
      from={teaser.hook.from}
      durationInFrames={teaser.hook.durationInFrames + SCENE_TRANSITION_FRAMES}
    >
      <HookScene durationInFrames={teaser.hook.durationInFrames} />
    </Sequence>
    <Sequence
      name="Gameplay"
      from={teaser.gameplay.from}
      durationInFrames={
        teaser.gameplay.durationInFrames + SCENE_TRANSITION_FRAMES
      }
    >
      <GameplayScene durationInFrames={teaser.gameplay.durationInFrames} />
    </Sequence>
    <Sequence name="Close" {...teaser.close}>
      <CloseScene durationInFrames={teaser.close.durationInFrames} />
    </Sequence>
  </AbsoluteFill>
);
