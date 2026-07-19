import { BrandCanvas } from "../components/BrandCanvas";
import { Screen } from "../components/Screen";
import {
  AnimatedTitle,
  Eyebrow,
  ProofChip,
  SceneNumber,
} from "../components/Typography";

export const StartScene = ({
  durationInFrames,
}: {
  durationInFrames: number;
}) => (
  <BrandCanvas durationInFrames={durationInFrames}>
    <div className="safe-area scene-grid scene-grid--start">
      <div className="scene-copy scene-copy--left">
        <SceneNumber value="01" />
        <Eyebrow>Start a route</Eyebrow>
        <AnimatedTitle className="scene-title">
          Choose the
          <br />
          kind of path
          <br />
          you want
        </AnimatedTitle>
        <p className="scene-body">
          Pick a difficulty, keep the whole atlas open, or focus the start and
          goal on one of ten topics.
        </p>
        <div className="chip-stack">
          <ProofChip tone="signal">Easy · Normal · Hard</ProofChip>
          <ProofChip tone="ochre">10 optional topics</ProofChip>
          <ProofChip tone="moss">Start · Goal · Open path</ProofChip>
        </div>
      </div>
      <Screen
        asset="images/setup-current.png"
        alt="Current Webwoven route setup"
        className="start-screen"
        fit="contain"
        fromScale={1.02}
        toScale={1.07}
      />
      <div className="screen-callout screen-callout--solo">
        <span>Current setup</span>
        Normal · Any category
      </div>
    </div>
  </BrandCanvas>
);
