import type { CSSProperties } from "react";
import { Img, interpolate, staticFile, useCurrentFrame } from "remotion";

type ScreenProps = {
  asset: string;
  alt: string;
  className?: string;
  fit?: "cover" | "contain";
  fromScale?: number;
  toScale?: number;
  style?: CSSProperties;
};

export const Screen = ({
  asset,
  alt,
  className = "",
  fit = "cover",
  fromScale = 1,
  toScale = 1.035,
  style,
}: ScreenProps) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, 420], [fromScale, toScale], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div className={`screen-frame ${className}`} style={style}>
      <Img
        src={staticFile(asset)}
        alt={alt}
        className="screen-frame__image"
        style={{ objectFit: fit, scale }}
      />
      <div className="screen-frame__topbar" aria-hidden="true">
        <i />
        <i />
        <i />
        <span>www.webwoven.org</span>
      </div>
    </div>
  );
};
