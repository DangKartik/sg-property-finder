import { describe, expect, it } from "vitest";
import { SCORE_BANDS, formatDate, formatNumber, formatPrice, scoreColor } from "./format";

describe("format helpers", () => {
  it("formats prices and numbers for Singapore", () => {
    expect(formatPrice(525000)).toContain("525,000");
    expect(formatPrice(null)).toBe("—");
    expect(formatNumber(1234.56, 1)).toBe("1,234.6");
    expect(formatNumber(undefined)).toBe("—");
  });

  it("formats valid dates and preserves invalid input", () => {
    expect(formatDate("2026-10-22T08:30:00+08:00")).not.toBe("—");
    expect(formatDate("not-a-date")).toBe("not-a-date");
    expect(formatDate(null)).toBe("—");
  });

  it("maps scores to the frozen colour bands", () => {
    expect(scoreColor(undefined)).toBe("#94a3b8");
    expect(scoreColor(75)).toBe("#0f766e");
    expect(scoreColor(60)).toBe("#65a30d");
    expect(scoreColor(45)).toBe("#f59e0b");
    expect(scoreColor(30)).toBe("#ea580c");
    expect(scoreColor(29)).toBe("#dc2626");
  });

  it("lists every colour band that the map uses in its legend", () => {
    expect(SCORE_BANDS).toHaveLength(5);
    for (const band of SCORE_BANDS) {
      expect(scoreColor(band.min)).toBe(band.color);
    }
  });
});
