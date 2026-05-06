from __future__ import annotations

import math
from datetime import date, timedelta

import pandas as pd


def coerce_run_frame(runs_df: pd.DataFrame) -> pd.DataFrame:
    frame = runs_df.copy()
    frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
    frame["start_date_local"] = pd.to_datetime(frame["start_date_local"])
    return frame.sort_values("start_date_local").reset_index(drop=True)


def apply_time_filter(
    runs_df: pd.DataFrame,
    preset: str,
    custom_range: tuple[date, date] | None,
) -> tuple[pd.DataFrame, pd.Timestamp, pd.Timestamp, str]:
    today = pd.Timestamp.today().normalize()
    if preset == "Last 7 days":
        start = today - pd.Timedelta(days=6)
        end = today
    elif preset == "Last 30 days":
        start = today - pd.Timedelta(days=29)
        end = today
    elif preset == "Year to date":
        start = pd.Timestamp(year=today.year, month=1, day=1)
        end = today
    elif preset == "Custom range" and custom_range:
        start = pd.Timestamp(custom_range[0])
        end = pd.Timestamp(custom_range[1])
    else:
        start = runs_df["date"].min()
        end = runs_df["date"].max()

    filtered = runs_df[runs_df["date"].between(start, end)].copy()
    label = f"{start.strftime('%d %b %Y')} to {end.strftime('%d %b %Y')}"
    return filtered, start, end, label


def apply_distance_filter(
    runs_df: pd.DataFrame,
    preset: str,
    custom_range: tuple[float, float] | None,
) -> pd.DataFrame:
    filtered = runs_df.copy()
    if preset == "Short runs (<5 km)":
        filtered = filtered[filtered["distance_km"] < 5]
    elif preset == "Medium runs (5 to 8 km)":
        filtered = filtered[filtered["distance_km"].between(5, 8)]
    elif preset == "Long runs (>8 km)":
        filtered = filtered[filtered["distance_km"] > 8]
    elif preset == "Custom distance" and custom_range:
        filtered = filtered[filtered["distance_km"].between(custom_range[0], custom_range[1])]
    return filtered.copy()


def previous_window(start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    span = end - start
    previous_end = start - pd.Timedelta(days=1)
    previous_start = previous_end - span
    return previous_start.normalize(), previous_end.normalize()


def slice_period(runs_df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return runs_df[runs_df["date"].between(start, end)].copy()


def summarize_metrics(runs_df: pd.DataFrame) -> dict[str, float | int | None]:
    if runs_df.empty:
        return {
            "runs": 0,
            "distance_km": 0.0,
            "avg_pace_sec_per_km": None,
            "longest_run_km": 0.0,
            "moving_time_h": 0.0,
            "elev_gain_m": 0.0,
            "avg_hr": None,
        }

    avg_hr = runs_df["avg_hr"].dropna()
    pace = runs_df["pace_sec_per_km"].dropna()
    return {
        "runs": int(len(runs_df)),
        "distance_km": float(runs_df["distance_km"].sum()),
        "avg_pace_sec_per_km": float(pace.mean()) if not pace.empty else None,
        "longest_run_km": float(runs_df["distance_km"].max()),
        "moving_time_h": float(runs_df["moving_time_min"].sum() / 60),
        "elev_gain_m": float(runs_df["elev_gain_m"].sum()),
        "avg_hr": float(avg_hr.mean()) if not avg_hr.empty else None,
    }


def percent_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100


def trend_state(current: float | None, previous: float | None, higher_is_better: bool) -> str:
    if current is None or previous is None:
        return "flat"
    if math.isclose(current, previous, rel_tol=1e-9, abs_tol=1e-9):
        return "flat"
    improved = current > previous if higher_is_better else current < previous
    return "up" if improved else "down"


def format_percent_chip(current: float, previous: float, higher_is_better: bool, label: str) -> tuple[str, str]:
    state = trend_state(current, previous, higher_is_better)
    change = percent_change(current, previous)
    if previous == 0 and current > 0:
        return state, f"▲ New vs {label}"
    if change is None:
        return "flat", f"• No baseline vs {label}"
    arrow = "▲" if state == "up" else "▼" if state == "down" else "•"
    return state, f"{arrow} {abs(change):.0f}% vs {label}"


def format_pace_delta(seconds_delta: float) -> str:
    minutes = int(seconds_delta // 60)
    seconds = int(round(seconds_delta % 60))
    if minutes > 0:
        return f"{minutes}:{seconds:02d} /km"
    return f"0:{seconds:02d} /km"


def format_pace_chip(current: float | None, previous: float | None, label: str) -> tuple[str, str]:
    if current is None or previous is None:
        return "flat", f"• No pace baseline vs {label}"
    delta = previous - current
    state = trend_state(current, previous, higher_is_better=False)
    if math.isclose(delta, 0, abs_tol=1e-9):
        return "flat", f"• Flat vs {label}"
    arrow = "▲" if state == "up" else "▼"
    speed_word = "faster" if delta > 0 else "slower"
    return state, f"{arrow} {format_pace_delta(abs(delta))} {speed_word} vs {label}"


def week_to_date_windows(today: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    week_start = today - pd.Timedelta(days=today.weekday())
    elapsed = today - week_start
    prev_start = week_start - pd.Timedelta(days=7)
    prev_end = prev_start + elapsed
    return week_start.normalize(), today.normalize(), prev_start.normalize(), prev_end.normalize()


def month_to_date_windows(today: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    month_start = today.replace(day=1)
    elapsed_days = (today - month_start).days
    prev_month_end = month_start - pd.Timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)
    prev_end = min(prev_month_start + pd.Timedelta(days=elapsed_days), prev_month_end)
    return month_start.normalize(), today.normalize(), prev_month_start.normalize(), prev_end.normalize()


def last_n_days_summary(runs_df: pd.DataFrame, days: int, offset_days: int = 0) -> dict[str, float | int | None]:
    end = pd.Timestamp.today().normalize() - pd.Timedelta(days=offset_days)
    start = end - pd.Timedelta(days=days - 1)
    return summarize_metrics(slice_period(runs_df, start, end))


def current_streak_days(runs_df: pd.DataFrame) -> int:
    if runs_df.empty:
        return 0
    run_dates = sorted({pd.Timestamp(value).normalize().date() for value in runs_df["date"]}, reverse=True)
    today = pd.Timestamp.today().normalize().date()
    if run_dates[0] < today - timedelta(days=1):
        return 0
    streak = 1
    for idx in range(len(run_dates) - 1):
        if run_dates[idx] - run_dates[idx + 1] == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def derive_narrative(runs_df: pd.DataFrame) -> str:
    recent = last_n_days_summary(runs_df, 28, offset_days=0)
    previous = last_n_days_summary(runs_df, 28, offset_days=28)
    volume_change = percent_change(recent["distance_km"], previous["distance_km"])
    recent_pace = recent["avg_pace_sec_per_km"]
    previous_pace = previous["avg_pace_sec_per_km"]
    pace_delta = (previous_pace - recent_pace) if recent_pace and previous_pace else None

    parts: list[str] = []
    if volume_change is not None:
        if volume_change >= 5:
            parts.append(f"Volume is trending up with {abs(volume_change):.0f}% more distance over the last 4 weeks.")
        elif volume_change <= -5:
            parts.append(f"Volume has eased by {abs(volume_change):.0f}% over the last 4 weeks.")
    if pace_delta is not None:
        if pace_delta >= 5:
            parts.append(f"Pace is sharpening too, at about {format_pace_delta(abs(pace_delta))} faster than the previous block.")
        elif pace_delta <= -5:
            parts.append(f"Pace has softened slightly, around {format_pace_delta(abs(pace_delta))} slower than the previous block.")

    if not parts:
        return "Training looks steady right now. Use the filters below to inspect consistency, volume, and route-level detail."
    return " ".join(parts)


def build_daily_totals(runs_df: pd.DataFrame) -> pd.DataFrame:
    if runs_df.empty:
        return pd.DataFrame(columns=["date", "distance_km", "run_count", "pace_sec_per_km"])
    daily = (
        runs_df.groupby("date", as_index=False)
        .agg(
            distance_km=("distance_km", "sum"),
            run_count=("id", "count"),
            pace_sec_per_km=("pace_sec_per_km", "mean"),
        )
        .sort_values("date")
    )
    daily["rolling_7d_distance"] = daily["distance_km"].rolling(window=7, min_periods=1).mean()
    return daily


def build_weekly_totals(runs_df: pd.DataFrame) -> pd.DataFrame:
    if runs_df.empty:
        return pd.DataFrame(columns=["week", "distance_km", "run_count", "rolling_distance"])
    weekly = runs_df.copy()
    weekly["week"] = weekly["date"] - pd.to_timedelta(weekly["date"].dt.weekday, unit="D")
    weekly["week"] = weekly["week"].dt.normalize()
    grouped = (
        weekly.groupby("week", as_index=False)
        .agg(distance_km=("distance_km", "sum"), run_count=("id", "count"))
        .sort_values("week")
    )
    all_weeks = pd.date_range(grouped["week"].min(), grouped["week"].max(), freq="W-MON")
    grouped = grouped.set_index("week").reindex(all_weeks, fill_value=0).rename_axis("week").reset_index()
    grouped["rolling_distance"] = grouped["distance_km"].rolling(window=4, min_periods=1).mean()
    return grouped


def build_monthly_totals(runs_df: pd.DataFrame) -> pd.DataFrame:
    if runs_df.empty:
        return pd.DataFrame(columns=["month", "distance_km", "run_count"])
    monthly = runs_df.copy()
    monthly["month"] = monthly["date"].dt.to_period("M").dt.start_time
    grouped = (
        monthly.groupby("month", as_index=False)
        .agg(distance_km=("distance_km", "sum"), run_count=("id", "count"))
        .sort_values("month")
    )
    all_months = pd.date_range(grouped["month"].min(), grouped["month"].max(), freq="MS")
    return grouped.set_index("month").reindex(all_months, fill_value=0).rename_axis("month").reset_index()


def build_rolling_bests_frame(
    runs_df: pd.DataFrame,
    thresholds_km: tuple[float, ...] = (3.0, 5.0, 10.0),
) -> pd.DataFrame:
    pace_df = runs_df.dropna(subset=["pace_sec_per_km"]).sort_values("date").copy()
    if pace_df.empty:
        return pd.DataFrame(columns=["date", "threshold_km", "best_pace_sec_per_km"])

    frames: list[pd.DataFrame] = []
    for threshold in thresholds_km:
        threshold_runs = pace_df[pace_df["distance_km"] >= threshold].copy()
        if threshold_runs.empty:
            continue
        threshold_runs["best_pace_sec_per_km"] = threshold_runs["pace_sec_per_km"].cummin()
        threshold_runs["threshold_km"] = f"{threshold:.0f}k+"
        frames.append(threshold_runs[["date", "threshold_km", "best_pace_sec_per_km"]])

    if not frames:
        return pd.DataFrame(columns=["date", "threshold_km", "best_pace_sec_per_km"])
    return pd.concat(frames, ignore_index=True)


def build_consistency_heatmap(runs_df: pd.DataFrame) -> pd.DataFrame:
    if runs_df.empty:
        return pd.DataFrame()
    heat = runs_df.copy()
    heat["week"] = heat["date"] - pd.to_timedelta(heat["date"].dt.weekday, unit="D")
    heat["week"] = heat["week"].dt.normalize()
    heat["weekday"] = heat["date"].dt.day_name().str[:3]
    grouped = (
        heat.groupby(["week", "weekday"], as_index=False)
        .agg(run_count=("id", "count"), distance_km=("distance_km", "sum"))
    )
    pivot = grouped.pivot(index="week", columns="weekday", values="distance_km").fillna(0)
    ordered_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for day_name in ordered_days:
        if day_name not in pivot.columns:
            pivot[day_name] = 0
    pivot = pivot[ordered_days].sort_index()
    all_weeks = pd.date_range(pivot.index.min(), pivot.index.max(), freq="W-MON")
    return pivot.reindex(all_weeks, fill_value=0)


def distance_band_definitions() -> dict[str, tuple[float, float | None]]:
    return {
        "3 to 5 km": (3.0, 5.0),
        "5 to 8 km": (5.0, 8.0),
        "8 to 12 km": (8.0, 12.0),
        "12 km+": (12.0, None),
    }


def format_distance_range_label(lower: float, upper: float | None) -> str:
    if upper is None:
        return f"{lower:.1f} km+"
    return f"{lower:.1f} to {upper:.1f} km"


def filter_runs_by_distance_range(runs_df: pd.DataFrame, lower: float, upper: float | None) -> pd.DataFrame:
    filtered = runs_df[runs_df["distance_km"] >= lower].copy()
    if upper is not None:
        filtered = filtered[filtered["distance_km"] < upper].copy()
    return filtered


def build_similar_runs_summary(runs_df: pd.DataFrame, lower: float, upper: float | None) -> tuple[str, str]:
    similar = filter_runs_by_distance_range(runs_df, lower, upper).sort_values("date").copy()
    if len(similar) < 4:
        return ("Not enough similar runs yet to compare progress confidently.", "")

    half = max(2, len(similar) // 2)
    early = similar.head(half)
    late = similar.tail(half)

    pace_text = ""
    if early["pace_sec_per_km"].notna().any() and late["pace_sec_per_km"].notna().any():
        early_pace = early["pace_sec_per_km"].dropna().mean()
        late_pace = late["pace_sec_per_km"].dropna().mean()
        delta = early_pace - late_pace
        direction = "faster" if delta > 0 else "slower"
        pace_text = f"Latest comparable runs are about {format_pace_delta(abs(delta))} {direction} than the earlier block."

    hr_text = ""
    if early["avg_hr"].notna().any() and late["avg_hr"].notna().any():
        early_hr = early["avg_hr"].dropna().mean()
        late_hr = late["avg_hr"].dropna().mean()
        delta_hr = late_hr - early_hr
        direction_hr = "higher" if delta_hr > 0 else "lower"
        hr_text = f"Average heart rate is {abs(delta_hr):.0f} bpm {direction_hr} across the latest block."

    if not pace_text and not hr_text:
        return ("Comparable run trend is available, but more heart-rate or pace data would improve the signal.", "")
    return (pace_text, hr_text)
