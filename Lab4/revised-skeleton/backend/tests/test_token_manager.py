"""Unit tests for OneMap token cache and automatic refresh."""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.adapter.one_map_token_manager import OneMapTokenManager


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Type": "application/json"}

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TokenManagerTests(unittest.TestCase):
    @patch("app.adapter.one_map_token_manager.urlopen")
    def test_token_is_cached_and_refreshed_after_expiry(self, mock_urlopen) -> None:
        expiry = int((datetime.now(timezone.utc) + timedelta(days=3)).timestamp())
        mock_urlopen.return_value = FakeResponse(
            {"access_token": "token-1", "expiry_timestamp": expiry}
        )
        manager = OneMapTokenManager("https://www.onemap.gov.sg", "user@example.com", "password")
        token = manager.getAccessToken()
        self.assertEqual(token, "token-1")
        self.assertEqual(manager.refreshCount, 1)
        self.assertTrue(manager.isTokenValid())

        self.assertEqual(manager.getAccessToken(), "token-1")
        self.assertEqual(manager.refreshCount, 1)

        manager.tokenExpiry = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.assertFalse(manager.isTokenValid())
        manager.getAccessToken()
        self.assertEqual(manager.refreshCount, 2)

    def test_missing_credentials_are_rejected(self) -> None:
        with self.assertRaises(Exception):
            OneMapTokenManager("https://www.onemap.gov.sg", "", "")


if __name__ == "__main__":
    unittest.main()
