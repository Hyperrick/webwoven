import { BrandCanvas } from "../components/BrandCanvas";
import { VideoScreen } from "../components/VideoScreen";
import { AnimatedTitle, Eyebrow, ProofChip } from "../components/Typography";

export const GameplayScene = ({
  durationInFrames,
}: {
  durationInFrames: number;
}) => (
  <BrandCanvas durationInFrames={durationInFrames}>
    <div className="safe-area gameplay-layout">
      <VideoScreen
        asset="captures/current-gameplay.mp4"
        trimBefore={90}
        className="gameplay-video"
      />
      <div className="gameplay-copy">
        <Eyebrow>Real knowledge. Real choices.</Eyebrow>
        <AnimatedTitle className="scene-title scene-title--small">
          Grow the map one named connection at a time.
        </AnimatedTitle>
        <div className="chip-stack">
          <ProofChip tone="signal">Inspect before moving</ProofChip>
          <ProofChip tone="moss">Sources stay visible</ProofChip>
        </div>
      </div>
    </div>
  </BrandCanvas>
);
