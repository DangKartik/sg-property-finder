import { describe, expect, it } from "vitest";
import {
  ALL_AMENITY_GROUP_IDS,
  amenityColor,
  filterAmenities,
} from "./amenities";
import type { AmenityPointDTO } from "../types/dto";

const points: AmenityPointDTO[] = [
  { name: "School A", category: "Primary School", latitude: 1.35, longitude: 103.94 },
  { name: "Hospital A", category: "Hospital", latitude: 1.35, longitude: 103.94 },
  { name: "Park A", category: "Park", latitude: 1.35, longitude: 103.94 },
  { name: "MRT A", category: "MRT", latitude: 1.35, longitude: 103.94 },
  { name: "Mall A", category: "Shopping Mall", latitude: 1.35, longitude: 103.94 },
];

describe("amenity layers", () => {
  it("returns all points when every group is visible", () => {
    expect(filterAmenities(points, true, ALL_AMENITY_GROUP_IDS)).toHaveLength(5);
  });

  it("filters by group and master toggle", () => {
    expect(filterAmenities(points, true, ["mrt", "malls"])).toHaveLength(2);
    expect(filterAmenities(points, false, ALL_AMENITY_GROUP_IDS)).toEqual([]);
  });

  it("assigns category colours", () => {
    expect(amenityColor("Primary School")).toBe("#2563eb");
    expect(amenityColor("Hospital")).toBe("#dc2626");
    expect(amenityColor("Park")).toBe("#16a34a");
    expect(amenityColor("MRT")).toBe("#7c3aed");
    expect(amenityColor("Shopping Mall")).toBe("#f59e0b");
    expect(amenityColor("Unknown")).toBe("#475467");
  });
});
