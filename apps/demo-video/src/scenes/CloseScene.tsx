import { BrandCanvas } from "../components/BrandCanvas";
import { BrandMark } from "../components/BrandMark";
import { Screen } from "../components/Screen";
import { AnimatedTitle, ProofChip } from "../components/Typography";

export const CloseScene = ({
  durationInFrames,
}: {
  durationInFrames: number;
}) => (
  <BrandCanvas durationInFrames={durationInFrames} dark>
    <Screen
      asset="images/results-current.png"
      alt="The current Webwoven route result"
      className="close-screen"
      fromScale={1.06}
      toScale={1.1}
    />
    <div className="close-shade" />
    <div className="close-content">
      <BrandMark inverted />
      <AnimatedTitle className="close-title">
        Connect anything.
        <br />
        Discover why it is connected.
      </AnimatedTitle>
      <ProofChip tone="signal">www.webwoven.org</ProofChip>
      <span className="close-note">
        No account needed · Desktop + mobile · Completely open-source
      </span>
    </div>
  </BrandCanvas>
);
