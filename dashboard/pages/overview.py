from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from dashboard.components import (
    render_goal_progress_card,
    render_insight_card,
    render_metric_card,
    render_mini_card,
    render_section_header,
    render_streak_card,
)
from dashboard.metrics import (
    current_streak_days,
    derive_narrative,
    format_pace_chip,
    format_percent_chip,
    month_to_date_windows,
    previous_window,
    slice_period,
    summarize_metrics,
    week_to_date_windows,
)
from strava_client import format_pace


def render_hero(profile_name: str, view_label: str) -> None:
    hero_updated = datetime.now().strftime("%d %b %Y %H:%M")
    st.markdown(
        f"""
        <div class="title-shell">
            <div class="section-kicker">Insight-first running dashboard</div>
            <div class="hero-row">
                <div>
                    <div class="hero-title">{profile_name}'s Strava Dashboard</div>
                    <div class="hero-subtitle">
                        Clean hierarchy, stronger comparisons, and better route context for your own training data.
                        The focus stays on consistency, progression, and what changed most recently.
                    </div>
                </div>
                <div class="hero-meta">
                    <span class="hero-chip">{view_label}</span>
                    <span class="hero-chip">Updated {hero_updated}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview(
    all_runs_df: pd.DataFrame,
    view_df: pd.DataFrame,
    previous_df: pd.DataFrame,
    time_preset: str,
    weekly_goal_km: float,
    monthly_goal_km: float,
    previous_start: pd.Timestamp | None,
    previous_end: pd.Timestamp | None,
) -> None:
    today = pd.Timestamp.today().normalize()
    cw_start, cw_end, pw_start, pw_end = week_to_date_windows(today)
    cm_start, cm_end, pm_start, pm_end = month_to_date_windows(today)
    current_week = summarize_metrics(slice_period(all_runs_df, cw_start, cw_end))
    previous_week = summarize_metrics(slice_period(all_runs_df, pw_start, pw_end))
    current_month = summarize_metrics(slice_period(all_runs_df, cm_start, cm_end))
    previous_month = summarize_metrics(slice_period(all_runs_df, pm_start, pm_end))

    render_section_header("Insights", "Derived comparisons first, so the dashboard explains what changed before showing raw data.")
    st.markdown(
        f"""
        <div class="narrative-strip">
            {derive_narrative(all_runs_df)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    insight_cols = st.columns(4)
    week_runs_state, week_runs_text = format_percent_chip(
        float(current_week["runs"]),
        float(previous_week["runs"]),
        higher_is_better=True,
        label="last week",
    )
    with insight_cols[0]:
        render_insight_card("Runs This Week", str(current_week["runs"]), "Week to date vs the same weekdays last week", week_runs_text, week_runs_state)

    week_distance_state, week_distance_text = format_percent_chip(
        float(current_week["distance_km"]),
        float(previous_week["distance_km"]),
        higher_is_better=True,
        label="last week",
    )
    with insight_cols[1]:
        render_insight_card("Distance This Week", f"{current_week['distance_km']:.1f} km", "Volume through today vs last week", week_distance_text, week_distance_state)

    month_pace_state, month_pace_text = format_pace_chip(
        current_month["avg_pace_sec_per_km"],
        previous_month["avg_pace_sec_per_km"],
        "last month",
    )
    with insight_cols[2]:
        render_insight_card("Pace This Month", format_pace(current_month["avg_pace_sec_per_km"]), "Month to date vs the same span last month", month_pace_text, month_pace_state)

    month_long_state, month_long_text = format_percent_chip(
        float(current_month["longest_run_km"]),
        float(previous_month["longest_run_km"]),
        higher_is_better=True,
        label="last month",
    )
    with insight_cols[3]:
        render_insight_card("Longest Run MTD", f"{current_month['longest_run_km']:.1f} km", "Best single run this month to date", month_long_text, month_long_state)

    current_view = summarize_metrics(view_df)
    previous_view = summarize_metrics(previous_df)
    comparison_label = (
        f"{previous_start.strftime('%d %b')} to {previous_end.strftime('%d %b')}"
        if previous_start is not None and previous_end is not None
        else "previous period"
    )

    render_section_header("Key Stats", "Primary metrics with cleaner hierarchy, icons, and comparison against the previous matching period.")
    kpi_cols = st.columns(4)

    runs_state, runs_trend = ("flat", "• All-time totals") if time_preset == "All time" else format_percent_chip(
        float(current_view["runs"]), float(previous_view["runs"]), higher_is_better=True, label=comparison_label
    )
    with kpi_cols[0]:
        render_metric_card("RUN", "Runs", str(current_view["runs"]), "Completed in current view", runs_trend, runs_state)

    dist_state, dist_trend = ("flat", "• All-time totals") if time_preset == "All time" else format_percent_chip(
        float(current_view["distance_km"]), float(previous_view["distance_km"]), higher_is_better=True, label=comparison_label
    )
    with kpi_cols[1]:
        render_metric_card("KM", "Distance", f"{current_view['distance_km']:.1f} km", "Total running volume", dist_trend, dist_state)

    pace_state, pace_trend = ("flat", "• All-time average") if time_preset == "All time" else format_pace_chip(
        current_view["avg_pace_sec_per_km"], previous_view["avg_pace_sec_per_km"], comparison_label
    )
    with kpi_cols[2]:
        render_metric_card("Pace", "Average Pace", format_pace(current_view["avg_pace_sec_per_km"]), "Lower is faster", pace_trend, pace_state)

    long_state, long_trend = ("flat", "• All-time best") if time_preset == "All time" else format_percent_chip(
        float(current_view["longest_run_km"]), float(previous_view["longest_run_km"]), higher_is_better=True, label=comparison_label
    )
    with kpi_cols[3]:
        render_metric_card("Long", "Longest Run", f"{current_view['longest_run_km']:.1f} km", "Best single-run distance", long_trend, long_state)

    goal_cols = st.columns(4)
    st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
    with goal_cols[0]:
        render_streak_card(current_streak_days(all_runs_df))
    with goal_cols[1]:
        render_goal_progress_card("Weekly Goal", float(current_week["distance_km"]), weekly_goal_km, "Progress toward this week's target")
    with goal_cols[2]:
        render_goal_progress_card("Monthly Goal", float(current_month["distance_km"]), monthly_goal_km, "Progress toward this month's target")
    with goal_cols[3]:
        render_mini_card("Moving Time", f"{current_view['moving_time_h']:.1f} h", "Across the current view")

    extra_metric_cols = st.columns(2)
    with extra_metric_cols[0]:
        render_mini_card("Elevation Gain", f"{current_view['elev_gain_m']:.0f} m", "Climbing accumulated")
    with extra_metric_cols[1]:
        avg_hr_text = f"{current_view['avg_hr']:.0f} bpm" if current_view["avg_hr"] is not None else "—"
        render_mini_card("Average HR", avg_hr_text, "Shown when Strava provides heart rate")
