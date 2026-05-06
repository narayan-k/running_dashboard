# Strava Running Dashboard

A lightweight Streamlit dashboard for your own Strava running data. This version is intentionally simple:

- no login UI
- no database
- no Firebase
- local token refresh using your Strava app credentials
- daily activity caching so it stays fast and avoids unnecessary API calls

## What you need

Create a Strava app at `https://www.strava.com/settings/api`, then make sure you have:

- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REFRESH_TOKEN`

Strava’s official docs say access tokens expire after six hours, and the refresh endpoint returns the latest refresh token, so this app stores the latest token state locally and reuses it on future runs.

Sources:

- https://developers.strava.com/docs/authentication
- https://developers.strava.com/docs/reference/

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your Strava values.

## Run

```bash
streamlit run streamlit_app.py
```

## Refresh behavior

- Access tokens are refreshed automatically when they are close to expiry.
- Activity data is cached locally for one day in `data/cache/activities_cache.json`.
- The `Refresh from Strava` button bypasses the daily cache.

## Notes

- This dashboard only focuses on runs.
- Route preview uses Strava’s summary polyline and draws it as a simple line chart, so there is no separate map token needed.
- The latest refresh token is written to `data/cache/token_state.json`. Keep that file private.
