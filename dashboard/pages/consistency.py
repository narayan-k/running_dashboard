from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts import build_heatmap_chart, build_histogram_chart, build_pace_distance_heatmap
from dashboard.components import render_mini_card, render_section_header
from dashboard.theme import PLOTLY_CONFIG
from strava_client import format_pace


def render_consistency_page(view_df: pd.DataFrame) -> None:
    render_section_header("Consistency and Distribution", "Training patterns, repeatability, and the shape of your run distances and paces.")
    heat_left, dist_right = st.columns([1.1, 1.1])
    with heat_left:
        st.plotly_chart(build_heatmap_chart(view_df), use_container_width=True, config=PLOTLY_CONFIG)
    with dist_right:
        st.plotly_chart(build_pace_distance_heatmap(view_df), use_container_width=True, config=PLOTLY_CONFIG)

    hist_left, hist_right = st.columns([1.1, 1.1])
    with hist_left:
        st.plotly_chart(build_histogram_chart(view_df, "distance_km", "Run Distance Distribution", "Distance (km)"), use_container_width=True, config=PLOTLY_CONFIG)
    with hist_right:
        pace_distribution = view_df.dropna(subset=["pace_sec_per_km"])
        st.plotly_chart(build_histogram_chart(pace_distribution, "pace_sec_per_km", "Pace Distribution", "Pace (min/km)"), use_container_width=True, config=PLOTLY_CONFIG)

    pr_col_left, pr_col_right = st.columns(2)
    with pr_col_left:
        fastest = view_df.dropna(subset=["pace_sec_per_km"]).sort_values("pace_sec_per_km").head(1)
        render_mini_card("Fastest Pace", format_pace(fastest.iloc[0]["pace_sec_per_km"]) if not fastest.empty else "—", fastest.iloc[0]["name"] if not fastest.empty else "No pace data available")
    with pr_col_right:
        longest = view_df.sort_values("distance_km", ascending=False).head(1)
        render_mini_card("Longest Run", f"{longest.iloc[0]['distance_km']:.1f} km" if not longest.empty else "—", longest.iloc[0]["name"] if not longest.empty else "No distance data available")
