import { BrandCanvas } from "../components/BrandCanvas";
import { Screen } from "../components/Screen";
import {
  AnimatedTitle,
  Eyebrow,
  ProofChip,
  SceneNumber,
} from "../components/Typography";

export const TrustScene = ({
  durationInFrames,
}: {
  durationInFrames: number;
}) => (
  <BrandCanvas durationInFrames={durationInFrames} dark>
    <Screen
      asset="images/gameplay-current.png"
      alt="Webwoven node map backed by the local atlas"
      className="trust-video"
      fromScale={1.04}
      toScale={1.08}
    />
    <div className="trust-shade" />
    <div className="safe-area trust-content">
      <SceneNumber value="06" />
      <Eyebrow>AI helped build it. AI does not play it.</Eyebrow>
      <AnimatedTitle className="scene-title scene-title--light">
        Every move comes from one checked local atlas.
      </AnimatedTitle>
      <div className="trust-stats">
        <div>
          <strong>3,970</strong>
          <span>playable things</span>
        </div>
        <div>
          <strong>22,402</strong>
          <span>named connections</span>
        </div>
        <div>
          <strong>0</strong>
          <span>runtime AI calls</span>
        </div>
      </div>
      <div className="chip-row">
        <ProofChip tone="paper">Deterministic rules</ProofChip>
        <ProofChip tone="moss">Source-backed facts</ProofChip>
      </div>
    </div>
  </BrandCanvas>
);
