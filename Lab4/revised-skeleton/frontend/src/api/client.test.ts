import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, apiCache } from "./client";

function jsonResponse(body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

describe("api client IndexedDB cache", () => {
  beforeEach(async () => {
    await apiCache.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("serves a repeated GET from IndexedDB without a second fetch", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(
        {
          success: true,
          data: [
            {
              criterionId: "PRICE",
              criterionName: "Affordability",
              unit: "SGD",
              direction: "MINIMIZE",
              bufferM: null,
              defaultWeight: 0.2,
            },
          ],
          warnings: [],
          error: null,
        },
        { ETag: '"snapshot-1"' },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const first = await api.getCriteria();
    const second = await api.getCriteria();

    expect(first.success).toBe(true);
    expect(second.data).toEqual(first.data);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("uses the cached envelope when the network is unavailable", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: [],
          warnings: [],
          error: null,
        }),
      )
      .mockRejectedValueOnce(new Error("offline"));
    vi.stubGlobal("fetch", fetchMock);

    await api.getAmenities();
    const cached = await apiCache.get("v1:GET:/api/v1/amenities");

    expect(cached).toBeDefined();
    if (cached) {
      cached.expiresAt = Date.now() - 1;
      await apiCache.set(cached);
    }

    const fallback = await api.getAmenities();
    expect(fallback.success).toBe(true);
    expect(
      fallback.warnings.some((warning) => warning.code === "STALE_CACHE"),
    ).toBe(true);
  });
});
