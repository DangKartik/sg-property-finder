import { describe, expect, it } from "vitest";
import { unavailableSubzoneIds } from "./subzones";
import type { MapDataDTO } from "../types/dto";

function mapData(
  features: Array<{ code?: string; available?: boolean }>,
): MapDataDTO {
  return {
    geojson: {
      type: "FeatureCollection",
      features: features.map((feature) => ({
        type: "Feature",
        properties: {
          subzoneCode: feature.code,
          dataAvailable: feature.available,
        },
        geometry: null,
      })),
    },
    scores: {},
    center: { latitude: 1.3521, longitude: 103.8198 },
  };
}

describe("subzone availability helper", () => {
  it("returns only subzones marked with insufficient data", () => {
    const data = mapData([
      { code: "TAMPINES01", available: true },
      { code: "WISZ01", available: false },
      { code: "CBSZ01", available: false },
    ]);

    expect(unavailableSubzoneIds(data)).toEqual(["WISZ01", "CBSZ01"]);
  });

  it("returns an empty list when every subzone is selectable", () => {
    const data = mapData([{ code: "BEDOK01", available: true }]);
    expect(unavailableSubzoneIds(data)).toEqual([]);
  });

  it("falls back to known codes for legacy cached geometry", () => {
    const data = mapData([
      { code: "WISZ01" },
      { code: "TAMPINES01" },
    ]);
    expect(unavailableSubzoneIds(data)).toEqual(["WISZ01"]);
  });

  it("handles missing map data safely", () => {
    expect(unavailableSubzoneIds(null)).toEqual([]);
  });
});
