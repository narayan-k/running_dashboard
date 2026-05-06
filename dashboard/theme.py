from __future__ import annotations

import streamlit as st

PRIMARY = "#FC4C02"
SUCCESS = "#22C55E"
DANGER = "#EF4444"
BG = "#F5F7FA"
CARD = "#FFFFFF"
TEXT = "#111827"
MUTED = "#6B7280"
BORDER = "#E5E7EB"
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
}


def configure_page() -> None:
    st.set_page_config(
        page_title="Strava Running Dashboard",
        page_icon="🏃",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_global_styles() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(252, 76, 2, 0.08), transparent 22%),
                linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
            color: {TEXT};
        }}
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"] {{
            display: none;
        }}
        .block-container {{
            padding-top: 0.9rem;
            padding-bottom: 2.25rem;
            padding-left: 1.7rem;
            padding-right: 1.7rem;
            max-width: 1480px;
        }}
        [data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.92);
            border-right: 1px solid {BORDER};
        }}
        [data-testid="stSidebar"] .block-container {{
            padding-top: 1.35rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }}
        .stButton > button {{
            border-radius: 14px;
            border: 1px solid rgba(17, 24, 39, 0.10);
            background: white;
            color: {TEXT};
            font-weight: 600;
            min-height: 48px;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
            transition: all 160ms ease;
        }}
        .stButton > button:hover {{
            border-color: rgba(252, 76, 2, 0.28);
            color: {PRIMARY};
            box-shadow: 0 10px 22px rgba(252, 76, 2, 0.10);
        }}
        div[data-baseweb="select"] > div,
        [data-testid="stNumberInputContainer"] {{
            border-radius: 14px;
            border: 1px solid rgba(17, 24, 39, 0.10);
            background: white;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.03);
        }}
        div[data-baseweb="select"] > div:hover,
        [data-testid="stNumberInputContainer"]:hover {{
            border-color: rgba(252, 76, 2, 0.26);
        }}
        .stCheckbox label {{
            font-weight: 500;
        }}
        .title-shell {{
            background: linear-gradient(135deg, rgba(252, 76, 2, 0.98), rgba(249, 115, 22, 0.96));
            color: white;
            border-radius: 30px;
            padding: 1.8rem 2rem;
            box-shadow: 0 26px 55px rgba(252, 76, 2, 0.20);
            margin-bottom: 1.6rem;
        }}
        .section-kicker {{
            color: rgba(255, 255, 255, 0.82);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.82rem;
        }}
        .hero-row {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 1.5rem;
            flex-wrap: wrap;
        }}
        .hero-title {{
            font-size: 3rem;
            font-weight: 760;
            line-height: 1.03;
            margin-top: 0.3rem;
        }}
        .hero-subtitle {{
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.92);
            max-width: 780px;
            margin-top: 0.7rem;
            line-height: 1.55;
        }}
        .hero-meta {{
            display: flex;
            gap: 0.7rem;
            flex-wrap: wrap;
            align-items: center;
        }}
        .hero-chip {{
            display: inline-flex;
            align-items: center;
            padding: 0.48rem 0.8rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.18);
            font-size: 0.88rem;
            font-weight: 600;
            color: white;
            backdrop-filter: blur(4px);
        }}
        .section-title {{
            font-size: 1.55rem;
            font-weight: 720;
            color: {TEXT};
            margin-bottom: 0.2rem;
        }}
        .section-subtitle {{
            font-size: 0.98rem;
            color: {MUTED};
            line-height: 1.55;
            margin-bottom: 1.15rem;
            max-width: 860px;
        }}
        .narrative-strip {{
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid {BORDER};
            border-radius: 20px;
            padding: 1rem 1.15rem;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.04);
            margin-bottom: 1.15rem;
            font-size: 1rem;
            line-height: 1.65;
            color: {TEXT};
        }}
        .insight-card, .metric-card, .mini-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 20px;
            padding: 1.2rem;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.04);
            transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
            height: 100%;
            margin-bottom: 0.95rem;
        }}
        .insight-card:hover, .metric-card:hover, .mini-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 18px 36px rgba(15, 23, 42, 0.08);
            border-color: rgba(252, 76, 2, 0.28);
        }}
        .card-label {{
            color: {MUTED};
            font-size: 0.88rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.45rem;
        }}
        .card-value {{
            color: {TEXT};
            font-size: 1.9rem;
            font-weight: 700;
            line-height: 1.08;
        }}
        .card-subtle {{
            color: {MUTED};
            font-size: 0.92rem;
            margin-top: 0.55rem;
        }}
        .trend-chip {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 999px;
            padding: 0.32rem 0.7rem;
            font-size: 0.82rem;
            font-weight: 600;
            margin-top: 0.8rem;
        }}
        .trend-up {{
            background: rgba(34, 197, 94, 0.14);
            color: {SUCCESS};
        }}
        .trend-down {{
            background: rgba(239, 68, 68, 0.12);
            color: {DANGER};
        }}
        .trend-flat {{
            background: rgba(107, 114, 128, 0.12);
            color: {MUTED};
        }}
        .goal-wrap {{
            margin-top: 1rem;
        }}
        .goal-label {{
            display: flex;
            justify-content: space-between;
            color: {TEXT};
            font-size: 0.94rem;
            margin-bottom: 0.42rem;
        }}
        .goal-bar {{
            width: 100%;
            height: 12px;
            border-radius: 999px;
            background: #E5E7EB;
            overflow: hidden;
        }}
        .goal-fill {{
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, {PRIMARY}, #fb923c);
        }}
        .goal-card-title {{
            display: flex;
            align-items: center;
            gap: 0.65rem;
            font-size: 1.65rem;
            font-weight: 760;
            color: {TEXT};
            margin: 0.55rem 0 0.55rem 0;
        }}
        .icon-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 44px;
            height: 44px;
            padding: 0 0.6rem;
            border-radius: 14px;
            background: rgba(252, 76, 2, 0.10);
            border: 1px solid rgba(252, 76, 2, 0.14);
            color: {PRIMARY};
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}
        .plan-day-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 1rem;
            min-height: 220px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
            margin-bottom: 0.9rem;
        }}
        .plan-day-name {{
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {MUTED};
            margin-bottom: 0.2rem;
        }}
        .plan-day-date {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {TEXT};
            margin-bottom: 0.8rem;
        }}
        .plan-tag {{
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.28rem 0.62rem;
            background: rgba(252, 76, 2, 0.10);
            color: {PRIMARY};
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 0.7rem;
        }}
        .plan-note {{
            color: {TEXT};
            font-size: 0.94rem;
            line-height: 1.5;
            margin-top: 0.55rem;
        }}
        .plan-meta {{
            color: {MUTED};
            font-size: 0.9rem;
            margin-top: 0.38rem;
        }}
        .plan-empty {{
            color: {MUTED};
            font-size: 0.94rem;
            line-height: 1.5;
            padding-top: 0.8rem;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.65rem;
            background: transparent;
            padding-bottom: 0.85rem;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: auto;
            padding: 0.72rem 1rem;
            border-radius: 999px;
            border: 1px solid {BORDER};
            background: rgba(255, 255, 255, 0.84);
            color: {MUTED};
            font-weight: 600;
            transition: all 160ms ease;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {TEXT};
            border-color: rgba(252, 76, 2, 0.3);
            background: rgba(255, 255, 255, 0.95);
        }}
        .stTabs [aria-selected="true"] {{
            background: rgba(252, 76, 2, 0.12);
            border-color: rgba(252, 76, 2, 0.30);
            color: {PRIMARY};
            box-shadow: 0 10px 22px rgba(252, 76, 2, 0.08);
        }}
        div[data-testid="stPlotlyChart"],
        div[data-testid="stDataFrame"] {{
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid {BORDER};
            border-radius: 22px;
            padding: 0.45rem;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.04);
        }}
        div[data-testid="stDataFrame"] {{
            padding: 0.25rem;
        }}
        .skeleton-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        .skeleton-card {{
            height: 110px;
            border-radius: 20px;
            background: linear-gradient(90deg, #edf2f7 25%, #f7fafc 37%, #edf2f7 63%);
            background-size: 400% 100%;
            animation: shimmer 1.4s ease infinite;
            border: 1px solid {BORDER};
        }}
        @keyframes shimmer {{
            0% {{ background-position: 100% 0; }}
            100% {{ background-position: -100% 0; }}
        }}
        @media (max-width: 900px) {{
            .hero-title {{
                font-size: 2.3rem;
            }}
            .skeleton-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
