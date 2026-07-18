import { Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { BrandCanvas } from "../components/BrandCanvas";
import {
  AnimatedTitle,
  Eyebrow,
  ProofChip,
  SceneNumber,
} from "../components/Typography";

const workstreams = [
  ["Product", "apps/web", "Svelte interface + route atlas"],
  ["Rules", "services/api", "Navigation + hints + scoring"],
  ["Knowledge", "services/pipeline", "Reviewed graph build"],
  ["Proof", "tests + docs", "Browser checks + build journal"],
] as const;

export const CodexScene = ({
  durationInFrames,
}: {
  durationInFrames: number;
}) => {
  const frame = useCurrentFrame();
  const introOpacity = interpolate(frame, [0, 330, 390], [1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const systemOpacity = interpolate(frame, [350, 410], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <BrandCanvas durationInFrames={durationInFrames}>
      <div className="safe-area codex-layout">
        <div className="codex-intro" style={{ opacity: introOpacity }}>
          <div className="codex-heading">
            <SceneNumber value="04" />
            <Eyebrow>Built with Codex</Eyebrow>
            <AnimatedTitle className="scene-title">
              GPT-5.6 Sol helped turn one idea into a working system.
            </AnimatedTitle>
            <p className="scene-body">
              I steered the goals, visual language, play tests, and final
              decisions. Codex accelerated implementation and review.
            </p>
            <div className="chip-row">
              <ProofChip tone="signal">Codex</ProofChip>
              <ProofChip tone="ink">GPT-5.6 Sol</ProofChip>
              <ProofChip tone="moss">Human-directed</ProofChip>
            </div>
          </div>
          <div className="codex-session-card">
            <small>Primary Codex build</small>
            <h3>Implement Webwoven game</h3>
            <dl>
              <div>
                <dt>Model</dt>
                <dd>GPT-5.6 Sol</dd>
              </div>
              <div>
                <dt>Scope</dt>
                <dd>Web · API · Data · Tests · Docs</dd>
              </div>
              <div>
                <dt>Result</dt>
                <dd>Working product</dd>
              </div>
            </dl>
          </div>
        </div>

        <div className="codex-system" style={{ opacity: systemOpacity }}>
          <div className="codex-system-heading">
            <SceneNumber value="04" />
            <Eyebrow>One idea, focused domains</Eyebrow>
            <AnimatedTitle delay={370} className="scene-title">
              Codex made the build faster without hiding the decisions.
            </AnimatedTitle>
          </div>
          <div className="architecture-sheet">
            <Img
              src={staticFile("images/architecture.svg")}
              alt="Webwoven system architecture"
            />
          </div>
          <div className="workstream-list">
            {workstreams.map(([label, path, copy], index) => {
              const progress = interpolate(
                frame,
                [460 + index * 55, 500 + index * 55],
                [0, 1],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                },
              );
              return (
                <div
                  className="workstream"
                  key={path}
                  style={{
                    opacity: progress,
                    translate: `${(1 - progress) * 50}px 0`,
                  }}
                >
                  <small>{label}</small>
                  <strong>{path}</strong>
                  <span>{copy}</span>
                </div>
              );
            })}
          </div>
          <div className="codex-proof-line">
            <span>idea</span>
            <i />
            <span>focused tasks</span>
            <i />
            <span>browser feedback</span>
            <i />
            <strong>working product</strong>
          </div>
        </div>
      </div>
    </BrandCanvas>
  );
};
