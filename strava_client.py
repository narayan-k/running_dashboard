from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()


STRAVA_BASE_URL = "https://www.strava.com/api/v3"
STRAVA_OAUTH_URL = "https://www.strava.com/oauth/token"
DAILY_CACHE_TTL = timedelta(days=1)
TOKEN_REFRESH_BUFFER = timedelta(hours=1)


class StravaConfigError(RuntimeError):
    pass


@dataclass
class StravaCredentials:
    client_id: str
    client_secret: str
    refresh_token: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _data_dir() -> Path:
    return Path(__file__).resolve().parent / "data" / "cache"


def _token_state_path() -> Path:
    return _data_dir() / "token_state.json"


def _activities_cache_path() -> Path:
    return _data_dir() / "activities_cache.json"


def _ensure_cache_dir() -> Path:
    path = _data_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_credentials() -> StravaCredentials:
    client_id = os.getenv("STRAVA_CLIENT_ID", "").strip()
    client_secret = os.getenv("STRAVA_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN", "").strip()

    state = load_json(_token_state_path())
    if isinstance(state, dict) and state.get("refresh_token"):
        refresh_token = str(state["refresh_token"]).strip()

    if not client_id or not client_secret or not refresh_token:
        raise StravaConfigError(
            "Missing Strava credentials. Add STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, "
            "and STRAVA_REFRESH_TOKEN to a local .env file."
        )

    return StravaCredentials(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
    )


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_json(path: Path, payload: dict[str, Any]) -> None:
    _ensure_cache_dir()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_valid_access_token(force_refresh: bool = False) -> str:
    creds = load_credentials()
    token_state = load_json(_token_state_path()) or {}

    access_token = token_state.get("access_token")
    expires_at = token_state.get("expires_at")

    if not force_refresh and access_token and expires_at:
        expiry = datetime.fromtimestamp(int(expires_at), tz=timezone.utc)
        if expiry - _utc_now() > TOKEN_REFRESH_BUFFER:
            return str(access_token)

    response = requests.post(
        STRAVA_OAUTH_URL,
        data={
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": creds.refresh_token,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    save_json(
        _token_state_path(),
        {
            "access_token": payload["access_token"],
            "refresh_token": payload["refresh_token"],
            "expires_at": payload["expires_at"],
            "updated_at": _utc_now().isoformat(),
        },
    )
    return str(payload["access_token"])


def strava_get(path: str, access_token: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(
        f"{STRAVA_BASE_URL}{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params or {},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_profile(force_refresh: bool = False) -> dict[str, Any]:
    access_token = get_valid_access_token(force_refresh=force_refresh)
    return strava_get("/athlete", access_token)


def _is_cache_fresh(path: Path) -> bool:
    payload = load_json(path)
    if not payload or "fetched_at" not in payload:
        return False
    fetched_at = datetime.fromisoformat(str(payload["fetched_at"]))
    return _utc_now() - fetched_at <= DAILY_CACHE_TTL


def fetch_all_activities(force_refresh: bool = False) -> list[dict[str, Any]]:
    cache_path = _activities_cache_path()
    if not force_refresh and _is_cache_fresh(cache_path):
        payload = load_json(cache_path)
        if payload and isinstance(payload.get("activities"), list):
            return payload["activities"]

    access_token = get_valid_access_token(force_refresh=force_refresh)
    activities: list[dict[str, Any]] = []
    page = 1

    while True:
        batch = strava_get(
            "/athlete/activities",
            access_token,
            params={"per_page": 200, "page": page},
        )
        if not batch:
            break
        activities.extend(batch)
        page += 1

    save_json(
        cache_path,
        {
            "fetched_at": _utc_now().isoformat(),
            "activity_count": len(activities),
            "activities": activities,
        },
    )
    return activities


def fetch_run_activities(force_refresh: bool = False) -> list[dict[str, Any]]:
    activities = fetch_all_activities(force_refresh=force_refresh)
    return [
        activity
        for activity in activities
        if activity.get("sport_type") == "Run" or activity.get("type") == "Run"
    ]


def _safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    if numerator in (None, 0) or denominator in (None, 0):
        return None
    return numerator / denominator


def enrich_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for run in runs:
        distance_m = float(run.get("distance") or 0.0)
        moving_time_s = int(run.get("moving_time") or 0)
        avg_speed_m_s = _safe_divide(distance_m, moving_time_s)
        pace_seconds = _safe_divide(moving_time_s, distance_m / 1000 if distance_m else None)
        start_date_local = run.get("start_date_local") or run.get("start_date")
        start_dt = datetime.fromisoformat(str(start_date_local).replace("Z", "+00:00"))

        enriched.append(
            {
                "id": run.get("id"),
                "name": run.get("name"),
                "date": start_dt.date().isoformat(),
                "start_date_local": start_dt.isoformat(),
                "distance_km": distance_m / 1000,
                "moving_time_min": moving_time_s / 60,
                "moving_time_s": moving_time_s,
                "elapsed_time_min": (int(run.get("elapsed_time") or 0)) / 60,
                "pace_sec_per_km": pace_seconds,
                "avg_speed_kmh": (avg_speed_m_s * 3.6) if avg_speed_m_s else None,
                "elev_gain_m": float(run.get("total_elevation_gain") or 0.0),
                "avg_hr": run.get("average_heartrate"),
                "max_hr": run.get("max_heartrate"),
                "calories": run.get("calories"),
                "achievement_count": run.get("achievement_count"),
                "kudos_count": run.get("kudos_count"),
                "comment_count": run.get("comment_count"),
                "suffer_score": run.get("suffer_score"),
                "location_city": run.get("location_city"),
                "location_country": run.get("location_country"),
                "map_summary_polyline": ((run.get("map") or {}).get("summary_polyline")),
            }
        )

    enriched.sort(key=lambda row: row["start_date_local"])
    return enriched


def format_pace(seconds_per_km: float | None) -> str:
    if seconds_per_km is None or math.isnan(seconds_per_km):
        return "—"
    minutes = int(seconds_per_km // 60)
    seconds = int(round(seconds_per_km % 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d} /km"

