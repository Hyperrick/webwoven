import { Sequence, interpolate, useCurrentFrame } from "remotion";
import { BrandCanvas } from "../components/BrandCanvas";
import { Screen } from "../components/Screen";
import { VideoScreen } from "../components/VideoScreen";
import {
  AnimatedTitle,
  Eyebrow,
  ProofChip,
  SceneNumber,
} from "../components/Typography";

export const ExplainScene = ({
  durationInFrames,
}: {
  durationInFrames: number;
}) => {
  const frame = useCurrentFrame();
  const desktopOpacity = interpolate(frame, [0, 560, 630], [1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const mobileOpacity = interpolate(frame, [570, 640], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <BrandCanvas durationInFrames={durationInFrames}>
      <div className="safe-area explain-layout">
        <div className="explain-heading" style={{ opacity: desktopOpacity }}>
          <SceneNumber value="02" />
          <Eyebrow>Every move explains itself</Eyebrow>
          <AnimatedTitle className="scene-title">
            The connection is part of the game.
          </AnimatedTitle>
        </div>
        <div
          className="explain-screen-wrap"
          style={{ opacity: desktopOpacity }}
        >
          <Sequence durationInFrames={650} layout="none">
            <VideoScreen
              asset="captures/current-gameplay.mp4"
              className="explain-screen"
            />
          </Sequence>
        </div>
        <div className="mobile-proof" style={{ opacity: mobileOpacity }}>
          <Screen
            asset="images/mobile-preview-current.png"
            alt="Webwoven mobile route preview"
            className="mobile-screen"
            fit="contain"
            fromScale={1}
            toScale={1.02}
          />
          <div className="mobile-proof__copy">
            <Eyebrow>Preview before moving</Eyebrow>
            <AnimatedTitle
              delay={610}
              className="scene-title scene-title--small"
            >
              Read the fact. See the picture. Check the source.
            </AnimatedTitle>
            <div className="chip-stack">
              <ProofChip tone="signal">Named relationship</ProofChip>
              <ProofChip tone="moss">Source stays one tap away</ProofChip>
              <ProofChip tone="ochre">
                3 hints, each with a point cost
              </ProofChip>
            </div>
          </div>
        </div>
        <Sequence from={500} durationInFrames={190}>
          <div className="fact-card">
            <span>Rosario</span>
            Lionel Messi was born in Rosario.
            <small>Inspect without spending a move</small>
          </div>
        </Sequence>
      </div>
    </BrandCanvas>
  );
};
