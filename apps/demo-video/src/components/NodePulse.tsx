import { Easing, interpolate, useCurrentFrame } from "remotion";
import { colors } from "../theme";

export const NodePulse = ({
  x,
  y,
  delay = 0,
  color = colors.signal,
  label,
}: {
  x: number;
  y: number;
  delay?: number;
  color?: string;
  label?: string;
}) => {
  const frame = useCurrentFrame();
  const animation = {
    extrapolateLeft: "clamp" as const,
    extrapolateRight: "clamp" as const,
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  };

  return (
    <div className="node-pulse" style={{ left: x, top: y }}>
      <div
        className="node-pulse__ring"
        style={{
          borderColor: color,
          opacity: interpolate(frame, [delay, delay + 20], [0, 1], animation),
          scale: interpolate(frame, [delay, delay + 20], [0.4, 1], animation),
        }}
      />
      <div className="node-pulse__dot" style={{ backgroundColor: color }} />
      {label ? (
        <span
          style={{
            opacity: interpolate(frame, [delay, delay + 20], [0, 1], animation),
          }}
        >
          {label}
        </span>
      ) : null}
    </div>
  );
};
