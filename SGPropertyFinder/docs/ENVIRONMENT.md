# Environment configuration

## Setup

```bash
cd SGPropertyFinder
cp .env.example .env
```

Fill in the values locally. `.env` is ignored by Git; only `.env.example` is
committed.

## Variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `ONEMAP_API_KEY` | No | Reserved for a future key-based OneMap gateway. |
| `ONEMAP_EMAIL` | Yes (OneMap) | OneMap account email used by the token endpoint. |
| `ONEMAP_PASSWORD` | Yes (OneMap) | OneMap account password used by the token endpoint. |
| `ONEMAP_BASE_URL` | Yes | Defaults to `https://www.onemap.gov.sg`. |
| `DATA_GOV_SG_API_KEY` | No | Optional data.gov.sg key; raises rate limits. |
| `DATA_GOV_SG_BASE_URL` | Yes | `https://api-production.data.gov.sg`. |
| `DATA_GOV_SG_REALTIME_BASE_URL` | Yes | `https://api-open.data.gov.sg/v2/real-time/api`. |
| `APP_ENV` | Yes | `development`, `test` or `production`. |
| `APP_HOST` | Yes | Local bind address. |
| `APP_PORT` | Yes | Local bind port. |
| `DATA_MAX_AGE_HOURS` | No | Refresh subzone/HDB snapshots from data.gov.sg after this many hours. Default `24`. |

## OneMap authentication note

The current OneMap API uses `POST /api/auth/post/getToken` with an email and
password to obtain a 3-day access token. `ONEMAP_API_KEY` is retained because it
was requested, but the adapter uses `ONEMAP_EMAIL` and `ONEMAP_PASSWORD` unless
a key-based gateway is added.

`OneMapTokenManager` caches the token in memory and refreshes it automatically
five minutes before expiry. `OneMapApiAdapter.getAccessToken()` is the entry
point for authorized requests. If OneMap returns HTTP 401, call
`invalidateToken()` and retry once.

## Production

Use the deployment platform's secret manager instead of a committed file. Never
log `ONEMAP_PASSWORD`, `ONEMAP_API_KEY` or `DATA_GOV_SG_API_KEY`.
