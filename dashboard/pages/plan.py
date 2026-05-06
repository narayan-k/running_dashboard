from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components import render_mini_card, render_plan_day_card, render_section_header
from dashboard.constants import SESSION_TYPE_OPTIONS
from dashboard.storage import load_running_plan, save_running_plan


def render_plan_page() -> None:
    render_section_header("Running Plan", "A lightweight weekly calendar for planning sessions, mileage, and notes alongside your activity dashboard.")

    running_plan = load_running_plan()
    today_ts = pd.Timestamp.today().normalize()
    current_week_start = today_ts - pd.Timedelta(days=today_ts.weekday())
    week_offset = st.slider("Week offset", min_value=-4, max_value=12, value=0, help="0 is this week, 1 is next week.")
    selected_week_start = current_week_start + pd.Timedelta(days=7 * week_offset)
    week_days = pd.date_range(selected_week_start, periods=7, freq="D")

    week_sessions = [running_plan.get(day.strftime("%Y-%m-%d")) for day in week_days]
    planned_distance = sum(float(session.get("distance_km", 0) or 0) for session in week_sessions if session)
    session_count = sum(1 for session in week_sessions if session)

    summary_cols = st.columns(3)
    with summary_cols[0]:
        render_mini_card("Week Of", selected_week_start.strftime("%d %b %Y"), "Current planning window")
    with summary_cols[1]:
        render_mini_card("Planned Sessions", str(session_count), "Days with a scheduled session")
    with summary_cols[2]:
        render_mini_card("Planned Distance", f"{planned_distance:.1f} km", "Total distance scheduled")

    calendar_cols = st.columns(7)
    for col, day in zip(calendar_cols, week_days):
        with col:
            render_plan_day_card(day, running_plan.get(day.strftime("%Y-%m-%d")))

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    editor_left, editor_right = st.columns([1.1, 0.9])

    with editor_left:
        st.markdown("### Edit Session")
        editable_day = st.selectbox(
            "Day",
            options=[day.strftime("%Y-%m-%d") for day in week_days],
            format_func=lambda value: pd.Timestamp(value).strftime("%A %d %b"),
        )
        existing_session = running_plan.get(editable_day, {})
        session_type = st.selectbox(
            "Session type",
            options=SESSION_TYPE_OPTIONS,
            index=(SESSION_TYPE_OPTIONS.index(existing_session.get("type")) if existing_session.get("type") in SESSION_TYPE_OPTIONS else 0),
        )
        session_title = st.text_input("Title", value=str(existing_session.get("title", "")))
        distance_value = float(existing_session.get("distance_km", 0.0) or 0.0)
        session_distance = st.number_input("Planned distance (km)", min_value=0.0, value=distance_value, step=0.5)
        session_effort = st.text_input("Effort / pace note", value=str(existing_session.get("effort", "")), placeholder="e.g. Easy, 6:00/km or RPE 7")
        session_notes = st.text_area("Notes", value=str(existing_session.get("notes", "")), height=110, placeholder="Warm-up, route, workout structure, reminders...")

        form_cols = st.columns(2)
        with form_cols[0]:
            if st.button("Save Session", use_container_width=True):
                running_plan[editable_day] = {
                    "type": session_type,
                    "title": session_title.strip() or session_type,
                    "distance_km": float(session_distance),
                    "effort": session_effort.strip(),
                    "notes": session_notes.strip(),
                }
                save_running_plan(running_plan)
                st.success(f"Saved plan for {editable_day}.")
        with form_cols[1]:
            if st.button("Clear Day", use_container_width=True):
                if editable_day in running_plan:
                    running_plan.pop(editable_day)
                    save_running_plan(running_plan)
                st.info(f"Cleared plan for {editable_day}.")

    with editor_right:
        st.markdown("### Planning Notes")
        st.markdown(
            """
            - Use `Week offset` to move through future weeks.
            - Add session type, distance, and notes for each day.
            - Everything saves locally in `data/cache/running_plan.json`.
            - Rest days can still have notes, like mobility or gym work.
            """
        )
        upcoming_plan_rows = []
        for day in week_days:
            key = day.strftime("%Y-%m-%d")
            session = running_plan.get(key)
            if not session:
                continue
            upcoming_plan_rows.append(
                {
                    "date": key,
                    "type": session.get("type", ""),
                    "title": session.get("title", ""),
                    "distance_km": session.get("distance_km", 0),
                    "effort": session.get("effort", ""),
                }
            )

        if upcoming_plan_rows:
            upcoming_df = pd.DataFrame(upcoming_plan_rows)
            st.dataframe(
                upcoming_df.rename(columns={"date": "Date", "type": "Type", "title": "Session", "distance_km": "KM", "effort": "Effort"}),
                use_container_width=True,
                hide_index=True,
                height=260,
            )
        else:
            st.info("No sessions planned for this week yet.")
