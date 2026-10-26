import { beforeEach, describe, expect, it } from "vitest";
import { ApiCache } from "./ApiCache";
import type { ApiEnvelope } from "../types/dto";

const envelope: ApiEnvelope<{ value: number }> = {
  success: true,
  data: { value: 42 },
  warnings: [],
  error: null,
};

describe("ApiCache", () => {
  const cache = new ApiCache();

  beforeEach(async () => {
    await cache.clear();
  });

  it("stores and retrieves an API envelope", async () => {
    await cache.set({
      key: "GET:/api/v1/criteria",
      envelope,
      etag: '"snapshot-1"',
      storedAt: Date.now(),
      expiresAt: Date.now() + 60_000,
    });

    const cached = await cache.get("GET:/api/v1/criteria");
    expect(cached?.envelope.data).toEqual({ value: 42 });
    expect(cached?.etag).toBe('"snapshot-1"');
  });

  it("deletes and prunes old entries", async () => {
    const now = Date.now();
    await cache.set({
      key: "old",
      envelope,
      etag: null,
      storedAt: now - 8 * 24 * 60 * 60 * 1000,
      expiresAt: now - 7 * 24 * 60 * 60 * 1000,
    });
    await cache.set({
      key: "new",
      envelope,
      etag: null,
      storedAt: now,
      expiresAt: now + 60_000,
    });

    await cache.prune();
    expect(await cache.get("old")).toBeUndefined();
    expect(await cache.get("new")).toBeDefined();

    await cache.delete("new");
    expect(await cache.get("new")).toBeUndefined();
  });
});
