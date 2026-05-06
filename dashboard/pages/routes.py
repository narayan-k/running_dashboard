from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts import build_route_map, decode_polyline_frame
from dashboard.components import build_activity_table, render_mini_card, render_section_header
from dashboard.constants import TABLE_SORT_OPTIONS
from dashboard.theme import PLOTLY_CONFIG
from strava_client import format_pace


def render_routes_page(view_df: pd.DataFrame) -> None:
    render_section_header("Routes and Activity Table", "Real map context, sortable activity details, and highlights for standout performances.")

    route_controls, table_controls = st.columns([1, 1])
    recent_runs = view_df.sort_values("start_date_local", ascending=False).head(40).copy()
    recent_runs["route_label"] = (
        recent_runs["date"].dt.strftime("%Y-%m-%d")
        + " · "
        + recent_runs["name"]
        + " · "
        + recent_runs["distance_km"].map(lambda value: f"{value:.1f} km")
    )

    with route_controls:
        selected_route = st.selectbox("Route preview", options=recent_runs["route_label"].tolist(), index=0)
    with table_controls:
        selected_sort = st.selectbox("Table sort", options=list(TABLE_SORT_OPTIONS.keys()), index=0)

    selected_row = recent_runs[recent_runs["route_label"] == selected_route].iloc[0]
    route_df = decode_polyline_frame(selected_row["map_summary_polyline"])

    route_left, route_right = st.columns([1.15, 0.85])
    with route_left:
        if route_df.empty:
            st.info("This run does not include route geometry in Strava's summary payload.")
        else:
            st.plotly_chart(build_route_map(route_df, selected_row["name"]), width="stretch", config=PLOTLY_CONFIG)

    with route_right:
        run_detail_cols = st.columns(2)
        with run_detail_cols[0]:
            render_mini_card("Distance", f"{selected_row['distance_km']:.1f} km", selected_row["date"].strftime("%d %b %Y"))
        with run_detail_cols[1]:
            render_mini_card("Pace", format_pace(selected_row["pace_sec_per_km"]), selected_row["name"])
        detail_cols_2 = st.columns(2)
        with detail_cols_2[0]:
            render_mini_card("Elevation", f"{selected_row['elev_gain_m']:.0f} m", "Selected route")
        with detail_cols_2[1]:
            avg_hr_value = selected_row["avg_hr"]
            render_mini_card("Avg HR", f"{avg_hr_value:.0f} bpm" if pd.notna(avg_hr_value) else "—", "Selected route")

    sort_column, ascending = TABLE_SORT_OPTIONS[selected_sort]
    activity_table_df = view_df.copy().sort_values(sort_column, ascending=ascending, na_position="last")
    st.dataframe(build_activity_table(activity_table_df), width="stretch", hide_index=True, height=360)
