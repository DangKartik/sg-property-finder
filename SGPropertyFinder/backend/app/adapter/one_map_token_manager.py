"""OneMap access-token cache with lazy automatic refresh."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OneMapAuthenticationError(RuntimeError):
    """Raised when OneMap token acquisition fails.

    The message never contains the account email, password or access token.
    """


class OneMapTokenManager:
    """Stereotype: adapter helper. Caches a OneMap token and refreshes it lazily.

    OneMap tokens are valid for about three days. `getAccessToken()` returns the
    cached token while it is valid and refreshes it automatically when it is
    missing, expired, or within `refreshSkewSeconds` of expiry.
    """

    baseUrl: str
    email: str
    password: str
    accessToken: str | None
    tokenExpiry: datetime | None
    refreshSkewSeconds: int
    timeoutSeconds: int
    refreshCount: int

    def __init__(
        self,
        baseUrl: str,
        email: str,
        password: str,
        refreshSkewSeconds: int = 300,
        timeoutSeconds: int = 20,
    ) -> None:
        """Create the token manager.

        Args:
            baseUrl: OneMap base URL, for example `https://www.onemap.gov.sg`.
            email: Registered OneMap account email.
            password: Registered OneMap account password.
            refreshSkewSeconds: Refresh this many seconds before expiry.
            timeoutSeconds: HTTP timeout for the token request.

        Failure handling:
            Missing credentials or a failed token request raise
            `OneMapAuthenticationError` when a token is requested.
        """
        if not email or not password:
            raise OneMapAuthenticationError(
                "ONEMAP_EMAIL and ONEMAP_PASSWORD must be set in the project .env file"
            )
        self.baseUrl = baseUrl.rstrip("/")
        self.email = email
        self.password = password
        self.accessToken = None
        self.tokenExpiry = None
        self.refreshSkewSeconds = refreshSkewSeconds
        self.timeoutSeconds = timeoutSeconds
        self.refreshCount = 0
        self._lock = threading.Lock()

    def isTokenValid(self) -> bool:
        """Return whether the cached token is still usable.

        Returns:
            bool: `True` when a token exists and is outside the refresh skew.

        Failure handling:
            Does not perform network I/O.
        """
        with self._lock:
            return self._isTokenValidLocked()

    def getAccessToken(self) -> str:
        """Return a valid token, refreshing automatically when necessary.

        Returns:
            str: A valid OneMap access token.

        Failure handling:
            Raise `OneMapAuthenticationError` when refresh fails.
        """
        with self._lock:
            if self._isTokenValidLocked():
                return self.accessToken  # type: ignore[return-value]
            return self._refreshLocked()

    def refreshToken(self) -> str:
        """Force a token refresh.

        Returns:
            str: The new OneMap access token.

        Failure handling:
            Raise `OneMapAuthenticationError` when authentication fails.
        """
        with self._lock:
            return self._refreshLocked()

    def invalidate(self) -> None:
        """Discard the cached token, forcing the next get to refresh.

        Returns:
            None.

        Failure handling:
            Safe to call at any time.
        """
        with self._lock:
            self.accessToken = None
            self.tokenExpiry = None

    def _isTokenValidLocked(self) -> bool:
        """Return validity while the caller holds `_lock`."""
        if not self.accessToken or self.tokenExpiry is None:
            return False
        refresh_at = datetime.now(timezone.utc) + timedelta(
            seconds=self.refreshSkewSeconds
        )
        return self.tokenExpiry > refresh_at

    def _refreshLocked(self) -> str:
        """Request a new token while the caller holds `_lock`."""
        url = f"{self.baseUrl}/api/auth/post/getToken"
        payload = json.dumps(
            {"email": self.email, "password": self.password}
        ).encode("utf-8")
        request = Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeoutSeconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise OneMapAuthenticationError(
                f"OneMap token request failed with HTTP {exc.code}"
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise OneMapAuthenticationError(
                "OneMap token request failed (network or response error)"
            ) from exc

        token = body.get("access_token")
        expiry_value = body.get("expiry_timestamp")
        if not token or expiry_value is None:
            raise OneMapAuthenticationError(
                "OneMap token response did not contain access_token/expiry_timestamp"
            )

        try:
            expiry_seconds = int(expiry_value)
            if expiry_seconds > 10_000_000_000:
                expiry_seconds //= 1000
            expiry = datetime.fromtimestamp(expiry_seconds, tz=timezone.utc)
        except (TypeError, ValueError, OSError) as exc:
            raise OneMapAuthenticationError(
                "OneMap token response contained an invalid expiry timestamp"
            ) from exc

        self.accessToken = token
        self.tokenExpiry = expiry
        self.refreshCount += 1
        return token
