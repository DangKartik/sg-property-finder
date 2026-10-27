import type { MapDataDTO } from "../types/dto";

interface SubzoneFeature {
  properties?: {
    subzoneCode?: string;
    dataAvailable?: boolean;
  };
}

// Fallback for map responses cached before the backend added `dataAvailable`.
// When the payload has availability metadata, the backend flag is authoritative.
const KNOWN_INSUFFICIENT_DATA_CODES = new Set([
  "WISZ01",
  "WISZ03",
  "WISZ02",
  "SISZ02",
  "QTSZ15",
  "THSZ02",
  "CBSZ01",
  "CCSZ01",
  "CHSZ03",
  "SLSZ03",
  "SMSZ04",
  "NESZ01",
  "TSSZ06",
]);

/** Return subzone codes that the backend marked as having insufficient data. */
export function unavailableSubzoneIds(mapData: MapDataDTO | null): string[] {
  const features =
    (mapData?.geojson as { features?: SubzoneFeature[] } | undefined)?.features ??
    [];
  const hasAvailabilityMetadata = features.some(
    (feature) => typeof feature.properties?.dataAvailable === "boolean",
  );
  const codes = features
    .map((feature) => feature.properties?.subzoneCode)
    .filter((code): code is string => Boolean(code));
  if (hasAvailabilityMetadata) {
    return features
      .filter(
        (feature) =>
          feature.properties?.subzoneCode &&
          feature.properties.dataAvailable === false,
      )
      .map((feature) => feature.properties?.subzoneCode as string);
  }
  return codes.filter((code) => KNOWN_INSUFFICIENT_DATA_CODES.has(code));
}
