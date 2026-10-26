"""Small TTL cache compatible with the subset of cachetools used by the app."""

from __future__ import annotations

import time
from typing import Callable, Generic, Iterator, TypeVar

try:
    from cachetools import TTLCache as _CachetoolsTTLCache
except ImportError:  # pragma: no cover - fallback for minimal environments
    _CachetoolsTTLCache = None

K = TypeVar("K")
V = TypeVar("V")


class TTLCache(Generic[K, V]):
    """Thread-unsafe TTL cache with cachetools-like accessors.

    The application uses one cache per process. Controls should not share
    request-specific values through this cache.
    """

    def __init__(self, maxsize: int = 256, ttl: float = 300.0, clock: Callable[[], float] | None = None) -> None:
        self.maxsize = maxsize
        self.ttl = ttl
        self._clock = clock or time.monotonic
        self._data: dict[K, tuple[float, V]] = {}
        self._backend = (
            _CachetoolsTTLCache(maxsize=maxsize, ttl=ttl)
            if _CachetoolsTTLCache is not None and clock is None
            else None
        )

    def _expired(self, expires_at: float) -> bool:
        return self._clock() >= expires_at

    def _purge(self) -> None:
        for key in [key for key, (expires_at, _) in self._data.items() if self._expired(expires_at)]:
            self._data.pop(key, None)

    def __len__(self) -> int:
        if self._backend is not None:
            return len(self._backend)
        self._purge()
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        if self._backend is not None:
            return key in self._backend
        self._purge()
        return key in self._data

    def __getitem__(self, key: K) -> V:
        if self._backend is not None:
            return self._backend[key]
        self._purge()
        if key not in self._data:
            raise KeyError(key)
        return self._data[key][1]

    def __setitem__(self, key: K, value: V) -> None:
        if self._backend is not None:
            self._backend[key] = value
            return
        self._purge()
        if len(self._data) >= self.maxsize and key not in self._data:
            oldest = min(self._data, key=lambda item: self._data[item][0])
            self._data.pop(oldest, None)
        self._data[key] = (self._clock() + self.ttl, value)

    def get(self, key: K, default: V | None = None) -> V | None:
        if self._backend is not None:
            return self._backend.get(key, default)
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self) -> None:
        if self._backend is not None:
            self._backend.clear()
        self._data.clear()

    def items(self) -> Iterator[tuple[K, V]]:
        if self._backend is not None:
            yield from self._backend.items()
            return
        self._purge()
        for key, (_, value) in list(self._data.items()):
            yield key, value
