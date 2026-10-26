import type { AmenityInfoDTO, AmenityPointDTO } from "../types/dto";

export interface AmenityGroup {
  id: string;
  label: string;
  color: string;
  categories: string[];
}

/** Display order and labels for the factsheet amenity sections. */
export const AMENITY_INFO_ORDER = [
  "Primary School",
  "Secondary School",
  "Tertiary School",
  "Polyclinic",
  "Hospital",
  "Park",
  "Shopping Mall",
  "MRT",
] as const;

export const AMENITY_INFO_LABELS: Record<string, string> = {
  "Primary School": "Primary Schools",
  "Secondary School": "Secondary Schools",
  "Tertiary School": "Tertiary Schools (JC/University)",
  Polyclinic: "Polyclinics",
  Hospital: "Hospitals",
  Park: "Parks",
  "Shopping Mall": "Malls",
  MRT: "MRTs / LRTs",
};

export interface AmenityInfoGroup {
  category: string;
  label: string;
  items: AmenityInfoDTO[];
}

/** Group nearby amenities by category, preserving a stable section order. */
export function groupAmenitiesByCategory(
  amenities: AmenityInfoDTO[],
): AmenityInfoGroup[] {
  const groups = new Map<string, AmenityInfoDTO[]>();
  for (const amenity of amenities) {
    const existing = groups.get(amenity.category);
    if (existing) {
      existing.push(amenity);
    } else {
      groups.set(amenity.category, [amenity]);
    }
  }

  const order = new Map<string, number>(
    AMENITY_INFO_ORDER.map((category, index) => [category, index]),
  );
  return [...groups.entries()]
    .sort(([left], [right]) => {
      const leftIndex = order.get(left);
      const rightIndex = order.get(right);
      if (leftIndex !== undefined && rightIndex !== undefined) {
        return leftIndex - rightIndex;
      }
      if (leftIndex !== undefined) return -1;
      if (rightIndex !== undefined) return 1;
      return left.localeCompare(right);
    })
    .map(([category, items]) => ({
      category,
      label: AMENITY_INFO_LABELS[category] ?? category,
      items: [...items].sort(
        (left, right) =>
          (left.distanceKm ?? Number.POSITIVE_INFINITY) -
          (right.distanceKm ?? Number.POSITIVE_INFINITY),
      ),
    }));
}

export const AMENITY_GROUPS: AmenityGroup[] = [
  {
    id: "schools",
    label: "Schools",
    color: "#2563eb",
    categories: ["Primary School", "Secondary School", "Tertiary School"],
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
export const AMENITY_FOCUS_RADIUS_KM = 2.0;

/** Great-circle distance between two coordinates in kilometres. */
export function distanceKm(
  origin: { latitude: number; longitude: number },
  destination: { latitude: number; longitude: number },
): number {
  const earthRadiusKm = 6371.0088;
  const toRadians = (value: number) => (value * Math.PI) / 180;
  const dLat = toRadians(destination.latitude - origin.latitude);
  const dLon = toRadians(destination.longitude - origin.longitude);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(origin.latitude)) *
      Math.cos(toRadians(destination.latitude)) *
      Math.sin(dLon / 2) ** 2;
  return 2 * earthRadiusKm * Math.asin(Math.min(1, Math.sqrt(a)));
}

/** Return amenities within the focus radius of a selected subzone anchor. */
export function nearbyAmenities(
  amenities: AmenityPointDTO[],
  center: { latitude: number; longitude: number } | null,
  radiusKm = AMENITY_FOCUS_RADIUS_KM,
): AmenityPointDTO[] {
  if (!center) {
    return [];
  }
  return amenities.filter(
    (amenity) => distanceKm(center, amenity) <= radiusKm,
  );
}

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
