import type { EntitySummary, ImageLicenseId } from "../api/types";

export interface ImageAttributionPresentation {
  creator: string;
  fileName: string;
  sourceUrl: string;
  licenseLabel: string;
  licenseUrl: string;
  attributionText: string;
  contextLabel?: string;
}

export interface EntityImageAttributionPresentation extends ImageAttributionPresentation {
  entityLabel: string;
}

const LICENSE_LABELS: Record<ImageLicenseId, string> = {
  PUBLIC_DOMAIN: "Public domain",
  CC0_1_0: "CC0 1.0",
  CC_BY_1_0: "CC BY 1.0",
  CC_BY_2_0: "CC BY 2.0",
  CC_BY_2_5: "CC BY 2.5",
  CC_BY_3_0: "CC BY 3.0",
  CC_BY_4_0: "CC BY 4.0",
  CC_BY_SA_1_0: "CC BY-SA 1.0",
  CC_BY_SA_2_0: "CC BY-SA 2.0",
  CC_BY_SA_2_5: "CC BY-SA 2.5",
  CC_BY_SA_3_0: "CC BY-SA 3.0",
  CC_BY_SA_4_0: "CC BY-SA 4.0",
};

export function imageAttributionFor(
  entity?: EntitySummary,
): ImageAttributionPresentation | undefined {
  const attribution = entity?.image_attribution;
  if (attribution === undefined) return undefined;

  const presentation: ImageAttributionPresentation = {
    creator: attribution.creator,
    fileName: attribution.file_name,
    sourceUrl: attribution.source_url,
    licenseLabel: LICENSE_LABELS[attribution.license_id],
    licenseUrl: attribution.license_url,
    attributionText: attribution.attribution_text,
  };
  return attribution.context_label
    ? { ...presentation, contextLabel: attribution.context_label }
    : presentation;
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
