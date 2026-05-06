from __future__ import annotations

import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import polyline
from plotly.subplots import make_subplots

from dashboard.metrics import (
    build_consistency_heatmap,
    build_monthly_totals,
    build_rolling_bests_frame,
    build_weekly_totals,
    filter_runs_by_distance_range,
)
from dashboard.theme import DANGER, PRIMARY, SUCCESS, TEXT
from strava_client import format_pace


def add_trend_line(fig: go.Figure, frame: pd.DataFrame, x_col: str, y_col: str, name: str) -> None:
    points = frame.dropna(subset=[y_col]).reset_index(drop=True)
    if len(points) < 2:
        return
    x_numeric = list(range(len(points)))
    y_values = points[y_col].tolist()
    x_mean = sum(x_numeric) / len(x_numeric)
    y_mean = sum(y_values) / len(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_numeric, y_values))
    denominator = sum((x - x_mean) ** 2 for x in x_numeric)
    if denominator == 0:
        return
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    trend = [intercept + slope * x for x in x_numeric]
    fig.add_trace(
        go.Scatter(
            x=points[x_col],
            y=trend,
            mode="lines",
            name=name,
            line=dict(color=SUCCESS, dash="dash", width=3),
        )
    )


def style_plotly_figure(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=16, r=16, t=54, b=16),
        font=dict(color=TEXT),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        title=dict(font=dict(size=22, color=TEXT)),
    )
    fig.update_xaxes(gridcolor="#EEF2F7", zerolinecolor="#EEF2F7")
    fig.update_yaxes(gridcolor="#EEF2F7", zerolinecolor="#EEF2F7")
    return fig


def apply_pace_axis_format(fig: go.Figure, axis: str = "y") -> go.Figure:
    pace_values = list(range(240, 541, 30))
    pace_labels = [format_pace(value).replace(" /km", "") for value in pace_values]
    update = {"tickmode": "array", "tickvals": pace_values, "ticktext": pace_labels}
    if axis == "y":
        fig.update_yaxes(**update)
    else:
        fig.update_xaxes(**update)
    return fig


def build_pace_over_time_chart(runs_df: pd.DataFrame) -> go.Figure:
    pace_df = runs_df.dropna(subset=["pace_sec_per_km"]).sort_values("date")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=pace_df["date"],
            y=pace_df["pace_sec_per_km"],
            mode="lines+markers",
            name="Pace",
            line=dict(color=PRIMARY, width=3),
            marker=dict(size=8, color=PRIMARY),
            customdata=pace_df["pace_sec_per_km"].map(format_pace),
            hovertemplate="%{x|%d %b %Y}<br>%{customdata}<extra></extra>",
        )
    )
    add_trend_line(fig, pace_df, "date", "pace_sec_per_km", "Trend")
    fig.update_layout(title="Pace Over Time", xaxis_title="Date", yaxis_title="Pace (min/km)")
    fig.update_yaxes(autorange="reversed")
    return apply_pace_axis_format(style_plotly_figure(fig))


def build_rolling_bests_chart(runs_df: pd.DataFrame) -> go.Figure:
    bests = build_rolling_bests_frame(runs_df)
    fig = go.Figure()
    if bests.empty:
        fig.update_layout(title="Rolling Best Pace by Distance")
        fig.update_yaxes(autorange="reversed")
        return apply_pace_axis_format(style_plotly_figure(fig))

    colors = {"3k+": PRIMARY, "5k+": SUCCESS, "10k+": "#0F172A"}
    for threshold_label in bests["threshold_km"].unique():
        frame = bests[bests["threshold_km"] == threshold_label]
        fig.add_trace(
            go.Scatter(
                x=frame["date"],
                y=frame["best_pace_sec_per_km"],
                mode="lines+markers",
                name=threshold_label,
                line=dict(color=colors.get(threshold_label, PRIMARY), width=3),
                marker=dict(size=7),
                customdata=frame["best_pace_sec_per_km"].map(format_pace),
                hovertemplate="%{x|%d %b %Y}<br>Best %{fullData.name}: %{customdata}<extra></extra>",
            )
        )

    fig.update_layout(title="Rolling Best Pace by Distance", xaxis_title="Date", yaxis_title="Best pace (min/km)")
    fig.update_yaxes(autorange="reversed")
    return apply_pace_axis_format(style_plotly_figure(fig))


def build_similar_runs_pace_chart(
    runs_df: pd.DataFrame,
    lower: float,
    upper: float | None,
    range_label: str,
) -> go.Figure:
    similar = filter_runs_by_distance_range(runs_df, lower, upper).dropna(subset=["pace_sec_per_km"]).sort_values("date")
    fig = go.Figure()
    if similar.empty:
        fig.update_layout(title=f"Pace Over Time · {range_label}")
        fig.update_yaxes(autorange="reversed")
        return apply_pace_axis_format(style_plotly_figure(fig))

    similar["rolling_pace"] = similar["pace_sec_per_km"].rolling(window=5, min_periods=1).mean()
    fig.add_trace(
        go.Scatter(
            x=similar["date"],
            y=similar["pace_sec_per_km"],
            mode="markers",
            name="Run pace",
            marker=dict(size=9, color=PRIMARY, opacity=0.7),
            customdata=similar[["name", "distance_km", "pace_sec_per_km", "elev_gain_m"]].values,
            hovertemplate="%{x|%d %b %Y}<br>%{customdata[0]}<br>%{customdata[1]:.1f} km · %{customdata[3]:.0f} m<br>%{customdata[2]:.0f} sec/km<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=similar["date"],
            y=similar["rolling_pace"],
            mode="lines",
            name="5-run avg",
            line=dict(color=SUCCESS, width=3),
        )
    )
    fig.update_layout(title=f"Comparable Run Pace · {range_label}", xaxis_title="Date", yaxis_title="Pace (min/km)")
    fig.update_yaxes(autorange="reversed")
    return apply_pace_axis_format(style_plotly_figure(fig))


def build_similar_runs_hr_chart(
    runs_df: pd.DataFrame,
    lower: float,
    upper: float | None,
    range_label: str,
) -> go.Figure:
    similar = filter_runs_by_distance_range(runs_df, lower, upper).dropna(subset=["avg_hr"]).sort_values("date")
    fig = go.Figure()
    if similar.empty:
        fig.update_layout(title=f"Heart Rate Over Time · {range_label}")
        return style_plotly_figure(fig)

    similar["rolling_hr"] = similar["avg_hr"].rolling(window=5, min_periods=1).mean()
    fig.add_trace(
        go.Scatter(
            x=similar["date"],
            y=similar["avg_hr"],
            mode="markers",
            name="Avg HR",
            marker=dict(size=9, color="#0F172A", opacity=0.7),
            customdata=similar[["name", "distance_km", "avg_hr", "pace_sec_per_km"]].values,
            hovertemplate="%{x|%d %b %Y}<br>%{customdata[0]}<br>%{customdata[1]:.1f} km<br>%{customdata[2]:.0f} bpm · %{customdata[3]:.0f} sec/km<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=similar["date"],
            y=similar["rolling_hr"],
            mode="lines",
            name="5-run avg",
            line=dict(color=PRIMARY, width=3),
        )
    )
    fig.update_layout(title=f"Comparable Run HR · {range_label}", xaxis_title="Date", yaxis_title="Average heart rate (bpm)")
    return style_plotly_figure(fig)


def build_weekly_distance_chart(runs_df: pd.DataFrame, weekly_goal_km: float, show_goal_line: bool) -> go.Figure:
    weekly = build_weekly_totals(runs_df)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=weekly["week"],
            y=weekly["distance_km"],
            name="Weekly distance",
            marker=dict(color="rgba(252, 76, 2, 0.82)"),
            hovertemplate="%{x|%d %b %Y}<br>%{y:.1f} km<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["rolling_distance"],
            mode="lines+markers",
            name="Rolling avg",
            line=dict(color=SUCCESS, width=3),
            marker=dict(size=7),
        )
    )
    if show_goal_line and weekly_goal_km > 0:
        fig.add_hline(
            y=weekly_goal_km,
            line_color="#0F172A",
            line_dash="dot",
            annotation_text=f"Goal {weekly_goal_km:.0f} km",
            annotation_position="top left",
        )
    fig.update_layout(title="Weekly Distance Trend", xaxis_title="Week", yaxis_title="Kilometres")
    return style_plotly_figure(fig)


def build_monthly_combo_chart(runs_df: pd.DataFrame) -> go.Figure:
    monthly = build_monthly_totals(runs_df)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=monthly["month"], y=monthly["distance_km"], name="Distance", marker=dict(color="rgba(252, 76, 2, 0.78)")), secondary_y=False)
    fig.add_trace(
        go.Scatter(
            x=monthly["month"],
            y=monthly["run_count"],
            name="Run count",
            mode="lines+markers",
            line=dict(color="#0F172A", width=3),
            marker=dict(size=8),
        ),
        secondary_y=True,
    )
    fig.update_layout(title="Monthly Distance and Run Count", xaxis_title="Month")
    fig.update_yaxes(title_text="Distance (km)", secondary_y=False)
    fig.update_yaxes(title_text="Runs", secondary_y=True)
    return style_plotly_figure(fig)


def build_heatmap_chart(runs_df: pd.DataFrame) -> go.Figure:
    pivot = build_consistency_heatmap(runs_df)
    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale=[[0.0, "#F3F4F6"], [0.3, "#FDD6C8"], [0.6, PRIMARY], [1.0, "#C2410C"]],
        labels=dict(color="Kilometres"),
    )
    fig.update_layout(title="Consistency Heatmap", xaxis_title="Day of week", yaxis_title="Week")
    return style_plotly_figure(fig, height=420)


def build_pace_distance_heatmap(runs_df: pd.DataFrame) -> go.Figure:
    pace_df = runs_df.dropna(subset=["pace_sec_per_km"]).copy()
    if pace_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Pace vs Distance Heatmap")
        return style_plotly_figure(fig, height=420)

    max_distance = max(5.0, float(math.ceil(pace_df["distance_km"].max())))
    distance_bins = list(pd.interval_range(start=0, end=max_distance + 1, freq=1, closed="left"))
    if len(distance_bins) < 2:
        distance_bins = list(pd.interval_range(start=0, end=max_distance + 2, freq=1, closed="left"))

    min_pace = float(math.floor(pace_df["pace_sec_per_km"].min() / 15.0) * 15.0)
    max_pace = float(math.ceil(pace_df["pace_sec_per_km"].max() / 15.0) * 15.0 + 15.0)
    pace_bins = list(pd.interval_range(start=min_pace, end=max_pace, freq=15, closed="left"))

    pace_df["distance_band"] = pd.cut(pace_df["distance_km"], bins=distance_bins)
    pace_df["pace_band"] = pd.cut(pace_df["pace_sec_per_km"], bins=pace_bins)
    grouped = pace_df.groupby(["pace_band", "distance_band"], observed=False).size().reset_index(name="run_count")
    pivot = grouped.pivot(index="pace_band", columns="distance_band", values="run_count").fillna(0)
    pivot.index = [f"{format_pace(interval.left).replace(' /km', '')} to {format_pace(interval.right).replace(' /km', '')}" for interval in pivot.index]
    pivot.columns = [f"{int(interval.left)}-{int(interval.right)} km" for interval in pivot.columns]

    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale=[[0.0, "#F8FAFC"], [0.25, "#FDD6C8"], [0.6, PRIMARY], [1.0, "#9A3412"]],
        labels=dict(x="Distance band", y="Pace band (min/km)", color="Runs"),
    )
    fig.update_layout(title="Pace vs Distance Heatmap", xaxis_title="Distance band", yaxis_title="Pace band (min/km)")
    fig.update_yaxes(autorange="reversed")
    return style_plotly_figure(fig, height=420)


def build_histogram_chart(runs_df: pd.DataFrame, column: str, title: str, xaxis_title: str) -> go.Figure:
    fig = px.histogram(runs_df, x=column, nbins=16, template="plotly_white")
    fig.update_traces(marker=dict(color=PRIMARY, line=dict(color="white", width=1)))
    fig.update_layout(title=title, xaxis_title=xaxis_title, yaxis_title="Runs")
    if column == "pace_sec_per_km":
        apply_pace_axis_format(fig, axis="x")
    return style_plotly_figure(fig, height=360)


def decode_polyline_frame(encoded: str | None) -> pd.DataFrame:
    if not encoded:
        return pd.DataFrame(columns=["lat", "lon", "seq"])
    coords = polyline.decode(encoded)
    return pd.DataFrame([{"lat": lat, "lon": lon, "seq": index} for index, (lat, lon) in enumerate(coords)])


def estimate_zoom(route_df: pd.DataFrame) -> float:
    if route_df.empty:
        return 11
    lat_span = max(route_df["lat"].max() - route_df["lat"].min(), 0.0001)
    lon_span = max(route_df["lon"].max() - route_df["lon"].min(), 0.0001)
    span = max(lat_span, lon_span)
    if span < 0.003:
        return 15
    if span < 0.008:
        return 14
    if span < 0.02:
        return 13
    if span < 0.05:
        return 12
    if span < 0.1:
        return 11
    return 10


def build_route_map(route_df: pd.DataFrame, run_name: str) -> go.Figure:
    fig = go.Figure()
    if route_df.empty:
        return fig

    start = route_df.iloc[0]
    end = route_df.iloc[-1]
    center = {"lat": route_df["lat"].mean(), "lon": route_df["lon"].mean()}
    fig.add_trace(go.Scattermapbox(lat=route_df["lat"], lon=route_df["lon"], mode="lines", name="Route", line=dict(color=PRIMARY, width=4), hoverinfo="skip"))
    fig.add_trace(go.Scattermapbox(lat=[start["lat"]], lon=[start["lon"]], mode="markers", name="Start", marker=dict(size=12, color=SUCCESS), text=["Start"], hovertemplate="%{text}<extra></extra>"))
    fig.add_trace(go.Scattermapbox(lat=[end["lat"]], lon=[end["lon"]], mode="markers", name="Finish", marker=dict(size=12, color=DANGER), text=["Finish"], hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(
        title=f"Route Preview: {run_name}",
        mapbox=dict(style="carto-positron", center=center, zoom=estimate_zoom(route_df)),
        margin=dict(l=16, r=16, t=54, b=16),
        height=460,
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig
