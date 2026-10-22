import { describe, expect, it } from "vitest";
import { decodePolyline } from "./polyline";

describe("decodePolyline", () => {
  it("decodes the canonical Google polyline example", () => {
    const points = decodePolyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@");
    expect(points).toHaveLength(3);
    expect(points[0][0]).toBeCloseTo(38.5, 5);
    expect(points[0][1]).toBeCloseTo(-120.2, 5);
    expect(points[2][0]).toBeCloseTo(43.252, 5);
    expect(points[2][1]).toBeCloseTo(-126.453, 5);
  });

  it("returns an empty array for missing geometry", () => {
    expect(decodePolyline(null)).toEqual([]);
    expect(decodePolyline("")).toEqual([]);
  });
});
