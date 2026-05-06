from __future__ import annotations

TIME_PRESET_OPTIONS = [
    "Last 30 days",
    "Last 7 days",
    "Year to date",
    "All time",
    "Custom range",
]

DISTANCE_PRESET_OPTIONS = [
    "All runs",
    "Short runs (<5 km)",
    "Medium runs (5 to 8 km)",
    "Long runs (>8 km)",
    "Custom distance",
]

COMPARE_MODE_OPTIONS = [
    "Preset bands",
    "Custom range",
]

SESSION_TYPE_OPTIONS = [
    "Easy",
    "Tempo",
    "Intervals",
    "Long Run",
    "Recovery",
    "Rest",
    "Race",
    "Strength",
]

TAB_LABELS = [
    "Performance",
    "Consistency",
    "Routes & Activity Log",
    "Running Plan",
]

TABLE_SORT_OPTIONS = {
    "Newest first": ("start_date_local", False),
    "Oldest first": ("start_date_local", True),
    "Longest distance": ("distance_km", False),
    "Shortest distance": ("distance_km", True),
    "Fastest pace": ("pace_sec_per_km", True),
    "Slowest pace": ("pace_sec_per_km", False),
}
