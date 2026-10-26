import { describe, expect, it } from "vitest";
import {
  ALL_AMENITY_GROUP_IDS,
  amenityColor,
  distanceKm,
  filterAmenities,
  groupAmenitiesByCategory,
  nearbyAmenities,
} from "./amenities";
import type { AmenityInfoDTO, AmenityPointDTO } from "../types/dto";

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

  it("only returns amenities within the focus radius", () => {
    const center = { latitude: 1.35, longitude: 103.94 };
    const near = { ...points[0], latitude: 1.351, longitude: 103.941 };
    const far = { ...points[1], latitude: 1.45, longitude: 104.04 };
    expect(distanceKm(center, near)).toBeLessThan(2);
    expect(nearbyAmenities([near, far], center)).toEqual([near]);
    expect(nearbyAmenities([near, far], null)).toEqual([]);
  });

  it("groups factsheet amenities by category in display order", () => {
    const info: AmenityInfoDTO[] = [
      {
        amenityName: "Mall B",
        category: "Shopping Mall",
        location: { latitude: 1.35, longitude: 103.94 },
        distanceKm: 0.8,
      },
      {
        amenityName: "Primary A",
        category: "Primary School",
        location: { latitude: 1.35, longitude: 103.94 },
        distanceKm: 0.3,
      },
      {
        amenityName: "Mall A",
        category: "Shopping Mall",
        location: { latitude: 1.35, longitude: 103.94 },
        distanceKm: 0.2,
      },
      {
        amenityName: "Mystery Place",
        category: "Other",
        location: { latitude: 1.35, longitude: 103.94 },
        distanceKm: 1.1,
      },
    ];

    const groups = groupAmenitiesByCategory(info);

    expect(groups.map((group) => group.label)).toEqual([
      "Primary Schools",
      "Malls",
      "Other",
    ]);
    expect(groups[1].items.map((item) => item.amenityName)).toEqual([
      "Mall A",
      "Mall B",
    ]);
  });
});
