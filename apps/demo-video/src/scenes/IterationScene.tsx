import { BrandCanvas } from "../components/BrandCanvas";
import { Screen } from "../components/Screen";
import { VideoScreen } from "../components/VideoScreen";
import {
  AnimatedTitle,
  Eyebrow,
  ProofChip,
  SceneNumber,
} from "../components/Typography";

export const IterationScene = ({
  durationInFrames,
}: {
  durationInFrames: number;
}) => (
  <BrandCanvas durationInFrames={durationInFrames}>
    <div className="safe-area iteration-layout">
      <div className="iteration-heading">
        <SceneNumber value="05" />
        <Eyebrow>Play. Notice. Improve.</Eyebrow>
        <AnimatedTitle className="scene-title">
          GPT-5.6 stayed in the loop after the first draft.
        </AnimatedTitle>
      </div>
      <div className="device-pair">
        <Screen
          asset="images/setup-current.png"
          alt="Current Webwoven route setup"
          className="device-desktop"
          fromScale={1.02}
          toScale={1.06}
        />
        <VideoScreen
          asset="captures/mobile-heartbeat.mp4"
          className="device-phone"
        />
      </div>
      <div className="iteration-chips">
        <ProofChip tone="signal">Play modes became obvious</ProofChip>
        <ProofChip tone="ochre">False dead ends became Back</ProofChip>
        <ProofChip tone="moss">Long labels stay complete</ProofChip>
        <ProofChip tone="ink">The reachable target pulses</ProofChip>
      </div>
    </div>
  </BrandCanvas>
);
