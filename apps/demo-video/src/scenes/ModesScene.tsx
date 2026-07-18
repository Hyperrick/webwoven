import { interpolate, useCurrentFrame } from "remotion";
import { BrandCanvas } from "../components/BrandCanvas";
import { Screen } from "../components/Screen";
import { Eyebrow, SceneNumber } from "../components/Typography";

const modes = [
  {
    start: -18,
    end: 174,
    number: "01",
    title: "Single player",
    copy: "Explore the atlas at your own speed.",
    asset: "images/landing-current.png",
    accent: "signal",
  },
  {
    start: 156,
    end: 291,
    number: "02",
    title: "Daily challenge",
    copy: "One shared route with a live score board.",
    asset: "images/daily-results-current.png",
    accent: "ochre",
  },
  {
    start: 273,
    end: 510,
    number: "03",
    title: "Multiplayer",
    copy: "Two to four explorers race on the same map.",
    asset: "images/relay-live-current.png",
    accent: "moss",
  },
] as const;

const phaseOpacity = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, start + 18, end - 18, end], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

export const ModesScene = ({
  durationInFrames,
}: {
  durationInFrames: number;
}) => {
  const frame = useCurrentFrame();

  return (
    <BrandCanvas durationInFrames={durationInFrames} dark>
      {modes.map((mode) => (
        <div
          className="mode-phase"
          key={mode.title}
          style={{ opacity: phaseOpacity(frame, mode.start, mode.end) }}
        >
          <Screen
            asset={mode.asset}
            alt={`Current Webwoven ${mode.title} screen`}
            className="modes-background"
            fromScale={1.01}
            toScale={1.045}
          />
          <div className="modes-shade" />
          <div className="safe-area mode-proof">
            <SceneNumber value="03" />
            <Eyebrow>Three ways in</Eyebrow>
            <div
              className={`mode-proof__number mode-proof__number--${mode.accent}`}
            >
              {mode.number}
            </div>
            <h2>{mode.title}</h2>
            <p>{mode.copy}</p>
          </div>
        </div>
      ))}
    </BrandCanvas>
  );
};
