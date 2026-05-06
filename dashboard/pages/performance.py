from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from dashboard.charts import (
    build_monthly_combo_chart,
    build_pace_over_time_chart,
    build_rolling_bests_chart,
    build_similar_runs_hr_chart,
    build_similar_runs_pace_chart,
    build_weekly_distance_chart,
)
from dashboard.components import render_section_header
from dashboard.constants import COMPARE_MODE_OPTIONS
from dashboard.metrics import (
    build_similar_runs_summary,
    distance_band_definitions,
    format_distance_range_label,
)
from dashboard.theme import PLOTLY_CONFIG


def render_performance_page(view_df: pd.DataFrame, weekly_goal_km: float, show_goal_line: bool) -> None:
    render_section_header("Charts", "Fewer, clearer charts focused on progress, performance, and the meaning behind the numbers.")
    top_left, top_right = st.columns(2)
    with top_left:
        st.plotly_chart(build_pace_over_time_chart(view_df), width="stretch", config=PLOTLY_CONFIG)
    with top_right:
        st.plotly_chart(build_weekly_distance_chart(view_df, weekly_goal_km, show_goal_line), width="stretch", config=PLOTLY_CONFIG)

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.plotly_chart(build_monthly_combo_chart(view_df), width="stretch", config=PLOTLY_CONFIG)
    with bottom_right:
        st.plotly_chart(build_rolling_bests_chart(view_df), width="stretch", config=PLOTLY_CONFIG)

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
    render_section_header("Comparable Run Progress", "Track pace and heart rate only against similar distances, so improvement is easier to spot.")

    distance_bands = distance_band_definitions()
    preset_labels = list(distance_bands.keys())
    compare_control_left, compare_control_right = st.columns([1.0, 1.4])
    with compare_control_left:
        compare_mode = st.radio("Comparison mode", COMPARE_MODE_OPTIONS, horizontal=True, key="similar_runs_compare_mode")

    if compare_mode == "Preset bands":
        with compare_control_right:
            default_band_index = preset_labels.index("5 to 8 km") if "5 to 8 km" in preset_labels else 0
            selected_band = st.selectbox("Comparable distance band", preset_labels, index=default_band_index, key="similar_runs_distance_band")
        selected_lower, selected_upper = distance_bands[selected_band]
        selected_range_label = selected_band
    else:
        min_distance = float(view_df["distance_km"].min())
        max_distance = float(view_df["distance_km"].max())
        slider_min = max(0.0, float(np.floor(min_distance * 2) / 2))
        slider_max = max(slider_min + 0.5, float(np.ceil(max_distance * 2) / 2))
        default_lower = min(max(5.0, slider_min), slider_max - 0.5)
        default_upper = min(max(8.0, default_lower + 0.5), slider_max)
        with compare_control_right:
            selected_lower, selected_upper = st.slider(
                "Custom comparable distance range (km)",
                min_value=slider_min,
                max_value=slider_max,
                value=(default_lower, default_upper),
                step=0.5,
                key="similar_runs_custom_distance_range",
            )
        selected_range_label = format_distance_range_label(float(selected_lower), float(selected_upper))

    selected_lower = float(selected_lower)
    selected_upper = None if compare_mode == "Preset bands" and selected_upper is None else float(selected_upper)
    similar_summary, hr_summary = build_similar_runs_summary(view_df, selected_lower, selected_upper)
    st.markdown(
        f"""
        <div class="narrative-strip">
            <strong>{selected_range_label}</strong>: {similar_summary}
            {f" {hr_summary}" if hr_summary else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

    compare_left, compare_right = st.columns(2)
    with compare_left:
        st.plotly_chart(build_similar_runs_pace_chart(view_df, selected_lower, selected_upper, selected_range_label), width="stretch", config=PLOTLY_CONFIG)
    with compare_right:
        st.plotly_chart(build_similar_runs_hr_chart(view_df, selected_lower, selected_upper, selected_range_label), width="stretch", config=PLOTLY_CONFIG)
