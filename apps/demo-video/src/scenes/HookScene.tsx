import { BrandCanvas } from "../components/BrandCanvas";
import { BrandMark } from "../components/BrandMark";
import { Screen } from "../components/Screen";
import { AnimatedTitle, Eyebrow, ProofChip } from "../components/Typography";

export const HookScene = ({
  durationInFrames,
}: {
  durationInFrames: number;
}) => (
  <BrandCanvas durationInFrames={durationInFrames} dark fadeIn={false}>
    <Screen
      asset="images/gameplay-current.png"
      alt="Webwoven node map during a live round"
      className="hook-screen"
      fromScale={1.03}
      toScale={1.08}
    />
    <div className="hook-shade" />
    <div className="safe-area hook-copy">
      <BrandMark inverted />
      <Eyebrow>A game of open knowledge</Eyebrow>
      <AnimatedTitle delay={8} className="hook-title">
        Find a path.
        <br />
        See <em>why.</em>
      </AnimatedTitle>
      <div className="hook-subtitle">
        Real things. Named connections. One living map.
      </div>
      <div className="chip-row">
        <ProofChip tone="paper">Start: Lionel Messi</ProofChip>
        <ProofChip tone="signal">Goal: Tour de France</ProofChip>
      </div>
    </div>
  </BrandCanvas>
);
