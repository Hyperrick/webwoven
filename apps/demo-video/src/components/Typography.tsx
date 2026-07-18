import type { ReactNode } from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";

export const Eyebrow = ({ children }: { children: ReactNode }) => (
  <div className="eyebrow">{children}</div>
);

export const AnimatedTitle = ({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) => {
  const frame = useCurrentFrame();
  const animation = {
    extrapolateLeft: "clamp" as const,
    extrapolateRight: "clamp" as const,
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  };

  return (
    <div
      className={`animated-title ${className}`}
      style={{
        opacity: interpolate(frame, [delay, delay + 20], [0, 1], animation),
        translate: `0 ${interpolate(frame, [delay, delay + 20], [54, 0], animation)}px`,
      }}
    >
      {children}
    </div>
  );
};

export const ProofChip = ({
  children,
  tone = "ink",
}: {
  children: ReactNode;
  tone?: "ink" | "signal" | "moss" | "ochre" | "paper";
}) => <div className={`proof-chip proof-chip--${tone}`}>{children}</div>;

export const SceneNumber = ({ value }: { value: string }) => (
  <div className="scene-number">{value}</div>
);
