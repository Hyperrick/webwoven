import { BrandCanvas } from "../components/BrandCanvas";
import { Screen } from "../components/Screen";
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
        <Screen
          asset="images/mobile-preview-current.png"
          alt="Webwoven phone node map"
          className="device-phone"
          fit="contain"
          fromScale={1}
          toScale={1.015}
        />
      </div>
      <div className="iteration-chips">
        <ProofChip tone="signal">Play modes became obvious</ProofChip>
        <ProofChip tone="ochre">Unfair loops were removed</ProofChip>
        <ProofChip tone="moss">Fact text became clearer</ProofChip>
        <ProofChip tone="ink">The phone map became touch-first</ProofChip>
      </div>
    </div>
  </BrandCanvas>
);
