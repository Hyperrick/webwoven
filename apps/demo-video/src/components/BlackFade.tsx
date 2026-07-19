import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

export const BLACK_FADE_FRAMES = 18;

export const BlackFade = ({ direction }: { direction: "in" | "out" }) => {
  const frame = useCurrentFrame();
  const opacityRange = direction === "in" ? [1, 0] : [0, 1];

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#000",
        opacity: interpolate(frame, [0, BLACK_FADE_FRAMES], opacityRange, {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        }),
        pointerEvents: "none",
        zIndex: 1000,
      }}
    />
  );
};
