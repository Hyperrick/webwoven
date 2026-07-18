import { Img, staticFile } from "remotion";

export const BrandMark = ({ inverted = false }: { inverted?: boolean }) => (
  <div className={inverted ? "brand-mark brand-mark--inverted" : "brand-mark"}>
    <Img src={staticFile("images/mark.svg")} className="brand-mark__icon" />
    <span>Webwoven</span>
  </div>
);
