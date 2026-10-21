"""Display-only live environment provider."""

from __future__ import annotations

from typing import Any

from app.adapter.data_gov_sg_adapter import DataGovSgAdapter
from app.core.cache import TTLCache


class LiveEnvironmentProvider:
    """Fetches real-time PM2.5, UVI and forecast values for display only."""

    def __init__(self, dataGovAdapter: DataGovSgAdapter, ttlSeconds: int = 300) -> None:
        """Create the provider with a short display cache."""
        self.dataGovAdapter = dataGovAdapter
        self.cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=8, ttl=ttlSeconds)

    def get(self, subzoneCode: str) -> dict[str, Any]:
        """Return live display values; failures are omitted rather than raised."""
        cached = self.cache.get("live")
        if cached is not None:
            return dict(cached)

        values: dict[str, Any] = {}
        try:
            pm25 = self.dataGovAdapter.fetchRealtime("pm25")
            items = pm25.get("data", {}).get("items", [])
            if items:
                readings = items[0].get("readings", {}).get("pm25_one_hourly", {})
                values["pm25"] = readings.get("national") or readings.get("central")
        except Exception:
            pass
        try:
            uv = self.dataGovAdapter.fetchRealtime("uv")
            records = uv.get("data", {}).get("records", [])
            if records and records[0].get("index"):
                values["uvi"] = records[0]["index"][0].get("value")
        except Exception:
            pass
        try:
            forecast = self.dataGovAdapter.fetchRealtime("twenty-four-hr-forecast")
            records = forecast.get("data", {}).get("records", [])
            if records:
                general = records[0].get("general", {}).get("forecast", {})
                values["forecastCode"] = general.get("code")
        except Exception:
            pass

        self.cache["live"] = values
        return dict(values)
