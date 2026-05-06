from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.theme import TEXT
from strava_client import format_pace


def render_loading_skeleton() -> st.delta_generator.DeltaGenerator:
    placeholder = st.empty()
    placeholder.markdown(
        """
        <div class="skeleton-grid">
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return placeholder


def render_section_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div style="margin:0.35rem 0 1rem 0;">
            <div class="section-title">{title}</div>
            <div class="section-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_card(label: str, value: str, context: str, trend_text: str, state: str) -> None:
    trend_class = {"up": "trend-up", "down": "trend-down", "flat": "trend-flat"}[state]
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="card-label">{label}</div>
            <div class="card-value">{value}</div>
            <div class="card-subtle">{context}</div>
            <div class="trend-chip {trend_class}">{trend_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(icon: str, label: str, value: str, helper: str, trend_text: str, state: str) -> None:
    trend_class = {"up": "trend-up", "down": "trend-down", "flat": "trend-flat"}[state]
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:0.8rem;">
                <div>
                    <div class="card-label">{label}</div>
                    <div class="card-value">{value}</div>
                </div>
                <div class="icon-badge">{icon}</div>
            </div>
            <div class="card-subtle">{helper}</div>
            <div class="trend-chip {trend_class}">{trend_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mini_card(label: str, value: str, helper: str) -> None:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="card-label">{label}</div>
            <div style="font-size:1.55rem; font-weight:700; color:{TEXT};">{value}</div>
            <div class="card-subtle">{helper}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_streak_card(streak_days: int) -> None:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="card-label">Streak</div>
            <div class="goal-card-title"><span>🔥</span><span>{streak_days} day streak</span></div>
            <div class="card-subtle">Consecutive running days through your latest logged run.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_goal_progress_card(label: str, current: float, target: float, helper: str) -> None:
    progress = 0.0 if target <= 0 else min(current / target, 1.0)
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="card-label">{label}</div>
            <div style="font-size:1.55rem; font-weight:700; color:{TEXT};">{current:.1f} / {target:.0f} km</div>
            <div class="card-subtle">{helper}</div>
            <div class="goal-wrap">
                <div class="goal-bar">
                    <div class="goal-fill" style="width:{progress * 100:.1f}%"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_plan_day_card(day: pd.Timestamp, session: dict[str, str | float] | None) -> None:
    if not session:
        st.markdown(
            f"""
            <div class="plan-day-card">
                <div class="plan-day-name">{day.strftime('%A')}</div>
                <div class="plan-day-date">{day.strftime('%d %b')}</div>
                <div class="plan-empty">No session planned yet. Use the editor below to add a workout, rest day, or note.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    title = str(session.get("title", "")).strip() or "Planned Session"
    session_type = str(session.get("type", "Easy")).strip() or "Easy"
    distance = session.get("distance_km", "")
    effort = str(session.get("effort", "")).strip()
    notes = str(session.get("notes", "")).strip()
    distance_text = ""
    if distance not in ("", None):
        try:
            distance_text = f"{float(distance):.1f} km planned"
        except (TypeError, ValueError):
            distance_text = ""

    st.markdown(
        f"""
        <div class="plan-day-card">
            <div class="plan-day-name">{day.strftime('%A')}</div>
            <div class="plan-day-date">{day.strftime('%d %b')}</div>
            <div class="plan-tag">{session_type}</div>
            <div style="font-size:1.08rem; font-weight:700; color:{TEXT};">{title}</div>
            <div class="plan-meta">{distance_text}</div>
            <div class="plan-meta">{effort}</div>
            <div class="plan-note">{notes if notes else "No notes added."}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_activity_table(runs_df: pd.DataFrame) -> pd.io.formats.style.Styler:
    table = runs_df.copy()
    fastest_run_id = table.dropna(subset=["pace_sec_per_km"]).sort_values("pace_sec_per_km").head(1)["id"].tolist()
    longest_run_id = table.sort_values("distance_km", ascending=False).head(1)["id"].tolist()
    highest_elev_id = table.sort_values("elev_gain_m", ascending=False).head(1)["id"].tolist()

    def highlight_label(row: pd.Series) -> str:
        flags: list[str] = []
        if row["id"] in fastest_run_id:
            flags.append("PR pace")
        if row["id"] in longest_run_id:
            flags.append("Longest")
        if row["id"] in highest_elev_id and row["elev_gain_m"] > 0:
            flags.append("Big climb")
        return ", ".join(flags)

    table["Highlight"] = table.apply(highlight_label, axis=1)
    table["Date"] = table["date"]
    table["Run"] = table["name"]
    table["Distance (km)"] = table["distance_km"]
    table["Pace"] = table["pace_sec_per_km"]
    table["Moving Time (min)"] = table["moving_time_min"]
    table["Elev (m)"] = table["elev_gain_m"]
    table["Avg HR"] = table["avg_hr"]
    table["Kudos"] = table["kudos_count"]
    display = table[["Date", "Run", "Distance (km)", "Pace", "Moving Time (min)", "Elev (m)", "Avg HR", "Kudos", "Highlight"]].copy()

    pace_values = display["Pace"].dropna()
    fast_cut = pace_values.quantile(0.33) if not pace_values.empty else None
    slow_cut = pace_values.quantile(0.67) if not pace_values.empty else None

    def pace_style(value: float) -> str:
        if pd.isna(value) or fast_cut is None or slow_cut is None:
            return ""
        if value <= fast_cut:
            return "background-color: rgba(34, 197, 94, 0.16); color: #166534; font-weight: 600;"
        if value >= slow_cut:
            return "background-color: rgba(239, 68, 68, 0.14); color: #991B1B; font-weight: 600;"
        return ""

    def highlight_style(value: str) -> str:
        if value:
            return "background-color: rgba(252, 76, 2, 0.10); color: #9A3412; font-weight: 600;"
        return ""

    return (
        display.style.format(
            {
                "Date": lambda value: pd.Timestamp(value).strftime("%Y-%m-%d"),
                "Distance (km)": "{:.1f}",
                "Pace": lambda value: format_pace(value) if pd.notna(value) else "—",
                "Moving Time (min)": "{:.0f}",
                "Elev (m)": "{:.0f}",
                "Avg HR": lambda value: f"{value:.0f}" if pd.notna(value) else "—",
                "Kudos": "{:.0f}",
            }
        )
        .applymap(pace_style, subset=["Pace"])
        .applymap(highlight_style, subset=["Highlight"])
    )
