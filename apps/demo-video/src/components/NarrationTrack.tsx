import { Audio } from "@remotion/media";
import { staticFile } from "remotion";

export type NarrationProps = {
  voiceoverFile?: string;
  narrationPlaybackRate?: number;
};

export const NarrationTrack = ({
  voiceoverFile,
  narrationPlaybackRate = 1,
}: NarrationProps) => {
  if (!voiceoverFile) {
    return null;
  }

  return (
    <Audio
      playbackRate={narrationPlaybackRate}
      src={staticFile(voiceoverFile)}
    />
  );
};
