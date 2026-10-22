import type { AmenityPointDTO } from "../types/dto";

export interface AmenityGroup {
  id: string;
  label: string;
  color: string;
  categories: string[];
}

export const AMENITY_GROUPS: AmenityGroup[] = [
  {
    id: "schools",
    label: "Schools",
    color: "#2563eb",
    categories: ["Primary School", "Secondary School"],
  },
  {
    id: "healthcare",
    label: "Healthcare",
    color: "#dc2626",
    categories: ["Polyclinic", "Hospital"],
  },
  {
    id: "parks",
    label: "Parks",
    color: "#16a34a",
    categories: ["Park"],
  },
  {
    id: "mrt",
    label: "MRT / LRT",
    color: "#7c3aed",
    categories: ["MRT"],
  },
  {
    id: "malls",
    label: "Malls",
    color: "#f59e0b",
    categories: ["Shopping Mall"],
  },
];

export const ALL_AMENITY_GROUP_IDS = AMENITY_GROUPS.map((group) => group.id);

/** Filter amenity points by the master toggle and active category groups. */
export function filterAmenities(
  amenities: AmenityPointDTO[],
  showAmenities: boolean,
  visibleGroups: string[],
): AmenityPointDTO[] {
  if (!showAmenities) {
    return [];
  }
  const activeGroups = new Set(visibleGroups);
  const activeCategories = new Set(
    AMENITY_GROUPS.filter((group) => activeGroups.has(group.id)).flatMap(
      (group) => group.categories,
    ),
  );
  return amenities.filter((amenity) => activeCategories.has(amenity.category));
}

/** Return the marker colour for an amenity category. */
export function amenityColor(category: string): string {
  for (const group of AMENITY_GROUPS) {
    if (group.categories.includes(category)) {
      return group.color;
    }
  }
  return "#475467";
}
