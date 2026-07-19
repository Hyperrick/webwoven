import type { CSSProperties, ReactNode } from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { colors } from "../theme";

type BrandCanvasProps = {
  children: ReactNode;
  durationInFrames: number;
  dark?: boolean;
  fadeIn?: boolean;
  style?: CSSProperties;
};

export const BrandCanvas = ({
  children,
  durationInFrames,
  dark = false,
  fadeIn = true,
  style,
}: BrandCanvasProps) => {
  const frame = useCurrentFrame();
  const fadeFrames = Math.min(12, Math.max(1, durationInFrames - 1));
  const opacity = fadeIn
    ? interpolate(frame, [0, fadeFrames], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;

  return (
    <AbsoluteFill
      className={dark ? "brand-canvas brand-canvas--dark" : "brand-canvas"}
      style={style}
    >
      <AbsoluteFill style={{ opacity }}>
        <RouteField color={dark ? colors.paper : colors.ink} />
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const RouteField = ({ color }: { color: string }) => {
  const frame = useCurrentFrame();
  const dashOffset = interpolate(frame, [0, 240], [150, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <svg
      className="route-field"
      viewBox="0 0 1920 1080"
      aria-hidden="true"
      style={{ color }}
    >
      <path
        d="M-80 850 C240 760 310 360 650 420 S1040 820 1390 590 S1700 260 2010 350"
        pathLength="300"
        style={{ strokeDashoffset: dashOffset }}
      />
      <path
        d="M80 210 C360 330 520 180 790 260 S1190 600 1440 450 S1690 190 1980 150"
        pathLength="300"
        style={{ strokeDashoffset: dashOffset + 70 }}
      />
      {[220, 650, 1010, 1390, 1710].map((x, index) => (
        <circle key={x} cx={x} cy={[720, 420, 660, 590, 310][index]} r="8" />
      ))}
    </svg>
  );
};
