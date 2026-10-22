import Dexie, { type Table } from "dexie";
import type { ApiEnvelope } from "../types/dto";

/** One persisted API response and its HTTP cache metadata. */
export interface CachedApiResponse {
  key: string;
  envelope: ApiEnvelope<unknown>;
  etag: string | null;
  storedAt: number;
  expiresAt: number;
}

class ApiCacheDatabase extends Dexie {
  responses!: Table<CachedApiResponse, string>;

  constructor() {
    super("sgpropfinder-api-cache");
    this.version(1).stores({
      responses: "key, storedAt, expiresAt",
    });
  }
}

/**
 * Stereotype: Container.
 * Dexie/IndexedDB persistence for API envelopes. Failures are non-fatal: the
 * API client falls back to the network when IndexedDB is unavailable.
 */
export class ApiCache {
  private readonly db = new ApiCacheDatabase();

  async get(key: string): Promise<CachedApiResponse | undefined> {
    try {
      return await this.db.responses.get(key);
    } catch {
      return undefined;
    }
  }

  async set(entry: CachedApiResponse): Promise<void> {
    try {
      await this.db.responses.put(entry);
    } catch {
      // Caching is an optimisation; a private-mode/quota failure must not break requests.
    }
  }

  async delete(key: string): Promise<void> {
    try {
      await this.db.responses.delete(key);
    } catch {
      // Ignore cache failures.
    }
  }

  async clear(): Promise<void> {
    try {
      await this.db.responses.clear();
    } catch {
      // Ignore cache failures.
    }
  }

  async prune(maxAgeMs = 7 * 24 * 60 * 60 * 1000): Promise<void> {
    const cutoff = Date.now() - maxAgeMs;
    try {
      await this.db.responses.where("storedAt").below(cutoff).delete();
    } catch {
      // Ignore cache failures.
    }
  }
}
