import type { EntitySummary, ImageLicenseId } from "../api/types";

export interface ImageAttributionPresentation {
  creator: string;
  fileName: string;
  sourceUrl: string;
  licenseLabel: string;
  licenseUrl: string;
  attributionText: string;
}

export interface EntityImageAttributionPresentation extends ImageAttributionPresentation {
  entityLabel: string;
}

const LICENSE_LABELS: Record<ImageLicenseId, string> = {
  PUBLIC_DOMAIN: "Public domain",
  CC0_1_0: "CC0 1.0",
  CC_BY_4_0: "CC BY 4.0",
};

export function imageAttributionFor(
  entity?: EntitySummary,
): ImageAttributionPresentation | undefined {
  const attribution = entity?.image_attribution;
  if (attribution === undefined) return undefined;

  return {
    creator: attribution.creator,
    fileName: attribution.file_name,
    sourceUrl: attribution.source_url,
    licenseLabel: LICENSE_LABELS[attribution.license_id],
    licenseUrl: attribution.license_url,
    attributionText: attribution.attribution_text,
  };
}

export function imageAttributionsFor(
  entities: readonly (EntitySummary | undefined)[],
): EntityImageAttributionPresentation[] {
  const seen = new Set<string>();
  const presentations: EntityImageAttributionPresentation[] = [];
  for (const entity of entities) {
    const attribution = imageAttributionFor(entity);
    if (!entity || !attribution || seen.has(attribution.sourceUrl)) continue;
    seen.add(attribution.sourceUrl);
    presentations.push({ ...attribution, entityLabel: entity.label });
  }
  return presentations;
}
