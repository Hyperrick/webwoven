import { Audio } from "@remotion/media";
import { staticFile } from "remotion";

export type NarrationProps = {
  voiceoverFile?: string;
};

export const NarrationTrack = ({ voiceoverFile }: NarrationProps) => {
  if (!voiceoverFile) {
    return null;
  }

  return <Audio src={staticFile(voiceoverFile)} />;
};
