from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from dashboard.components import render_loading_skeleton
from dashboard.constants import DISTANCE_PRESET_OPTIONS, TAB_LABELS, TIME_PRESET_OPTIONS
from dashboard.metrics import (
    apply_distance_filter,
    apply_time_filter,
    coerce_run_frame,
    previous_window,
    slice_period,
)
from dashboard.pages.consistency import render_consistency_page
from dashboard.pages.overview import render_hero, render_overview
from dashboard.pages.performance import render_performance_page
from dashboard.pages.plan import render_plan_page
from dashboard.pages.routes import render_routes_page
from dashboard.storage import (
    load_cache_timestamp,
    load_dashboard_data,
    load_ui_settings,
    save_ui_settings,
)
from dashboard.theme import configure_page, inject_global_styles
from strava_client import StravaConfigError


configure_page()
inject_global_styles()


st.sidebar.title("Controls")
refresh_now = st.sidebar.button("Refresh from Strava", use_container_width=True)
st.sidebar.caption("Daily caching stays on by default. Refresh bypasses the cache once.")

if refresh_now:
    load_dashboard_data.clear()

loading_placeholder = render_loading_skeleton()
try:
    with st.spinner("Loading running data from Strava..."):
        profile, all_runs_df = load_dashboard_data(force_refresh=refresh_now)
except StravaConfigError as exc:
    loading_placeholder.empty()
    st.error(str(exc))
    st.info("Create a local `.env` from `.env.example`, then rerun the app.")
    st.stop()
except Exception as exc:
    loading_placeholder.empty()
    st.error(f"Failed to load Strava data: {exc}")
    st.stop()
finally:
    loading_placeholder.empty()

try:
    all_runs_df = coerce_run_frame(all_runs_df)
except Exception as exc:
    st.error(f"Failed to prepare Strava data: {exc}")
    st.stop()

if all_runs_df.empty:
    st.warning("No run activities were returned from Strava.")
    st.stop()

cache_timestamp = load_cache_timestamp()
if cache_timestamp:
    st.sidebar.caption(f"Last activity sync: {cache_timestamp}")

time_preset = st.sidebar.selectbox(
    "Time window",
    options=TIME_PRESET_OPTIONS,
    index=0,
)

custom_dates: tuple[date, date] | None = None
if time_preset == "Custom range":
    default_start = (pd.Timestamp.today().normalize() - pd.Timedelta(days=29)).date()
    default_end = pd.Timestamp.today().normalize().date()
    selected_range = st.sidebar.date_input(
        "Custom dates",
        value=(default_start, default_end),
    )
    if isinstance(selected_range, (list, tuple)) and len(selected_range) == 2:
        custom_dates = (selected_range[0], selected_range[1])

distance_preset = st.sidebar.selectbox(
    "Distance focus",
    options=DISTANCE_PRESET_OPTIONS,
    index=0,
)

custom_distance: tuple[float, float] | None = None
distance_min = float(all_runs_df["distance_km"].min())
distance_max = float(all_runs_df["distance_km"].max())
if distance_preset == "Custom distance":
    custom_distance = st.sidebar.slider(
        "Distance range (km)",
        min_value=distance_min,
        max_value=distance_max,
        value=(distance_min, distance_max),
    )

st.sidebar.divider()
ui_settings = load_ui_settings()
weekly_goal_default = float(ui_settings.get("weekly_goal_km", 25.0))
monthly_goal_default = float(ui_settings.get("monthly_goal_km", 100.0))
show_goal_line_default = bool(ui_settings.get("show_goal_line", True))

weekly_goal_km = st.sidebar.number_input("Weekly goal (km)", min_value=0.0, value=weekly_goal_default, step=1.0)
monthly_goal_km = st.sidebar.number_input("Monthly goal (km)", min_value=0.0, value=monthly_goal_default, step=5.0)
show_goal_line = st.sidebar.checkbox("Show weekly goal line", value=show_goal_line_default)

updated_ui_settings = {
    "weekly_goal_km": float(weekly_goal_km),
    "monthly_goal_km": float(monthly_goal_km),
    "show_goal_line": bool(show_goal_line),
}
if updated_ui_settings != ui_settings:
    save_ui_settings(updated_ui_settings)

view_df, view_start, view_end, view_label = apply_time_filter(all_runs_df, time_preset, custom_dates)
view_df = apply_distance_filter(view_df, distance_preset, custom_distance)

previous_start: pd.Timestamp | None = None
previous_end: pd.Timestamp | None = None
previous_df = pd.DataFrame(columns=all_runs_df.columns)
if time_preset != "All time":
    previous_start, previous_end = previous_window(view_start, view_end)
    previous_df = apply_distance_filter(
        slice_period(all_runs_df, previous_start, previous_end),
        distance_preset,
        custom_distance,
    )

if view_df.empty:
    st.warning("No runs match the current filters.")
    st.stop()

profile_name = profile.get("firstname") or "My"
render_hero(profile_name, view_label)
render_overview(
    all_runs_df=all_runs_df,
    view_df=view_df,
    previous_df=previous_df,
    time_preset=time_preset,
    weekly_goal_km=weekly_goal_km,
    monthly_goal_km=monthly_goal_km,
    previous_start=previous_start,
    previous_end=previous_end,
)

performance_tab, consistency_tab, route_tab, plan_tab = st.tabs(TAB_LABELS)
with performance_tab:
    render_performance_page(view_df=view_df, weekly_goal_km=weekly_goal_km, show_goal_line=show_goal_line)
with consistency_tab:
    render_consistency_page(view_df=view_df)
with route_tab:
    render_routes_page(view_df=view_df)
with plan_tab:
    render_plan_page()
