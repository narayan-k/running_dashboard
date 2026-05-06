from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from strava_client import enrich_runs, fetch_profile, fetch_run_activities


@st.cache_data(show_spinner=False)
def load_dashboard_data(force_refresh: bool) -> tuple[dict, pd.DataFrame]:
    profile = fetch_profile(force_refresh=force_refresh)
    runs = enrich_runs(fetch_run_activities(force_refresh=force_refresh))
    return profile, pd.DataFrame(runs)


def load_cache_timestamp() -> str | None:
    path = Path("data/cache/activities_cache.json")
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    fetched_at = payload.get("fetched_at")
    if not fetched_at:
        return None
    try:
        timestamp = pd.to_datetime(fetched_at)
    except Exception:
        return None
    return timestamp.strftime("%d %b %Y %H:%M")


def settings_path() -> Path:
    return Path("data/cache/ui_settings.json")


def running_plan_path() -> Path:
    return Path("data/cache/running_plan.json")


def load_ui_settings() -> dict[str, float | bool]:
    path = settings_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def save_ui_settings(settings: dict[str, float | bool]) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def load_running_plan() -> dict[str, dict[str, str | float]]:
    path = running_plan_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def save_running_plan(plan: dict[str, dict[str, str | float]]) -> None:
    path = running_plan_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
