import type { CSSProperties } from "react";
import { Video } from "@remotion/media";
import { staticFile } from "remotion";

export const VideoScreen = ({
  asset,
  className = "",
  style,
  trimBefore = 0,
}: {
  asset: string;
  className?: string;
  style?: CSSProperties;
  trimBefore?: number;
}) => (
  <div className={`screen-frame ${className}`} style={style}>
    <Video
      src={staticFile(asset)}
      trimBefore={trimBefore}
      muted
      objectFit="cover"
      className="screen-frame__image"
    />
    <div className="screen-frame__topbar" aria-hidden="true">
      <i />
      <i />
      <i />
      <span>www.webwoven.org</span>
    </div>
  </div>
);
