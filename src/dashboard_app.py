from pathlib import Path
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from styles import inject_custom_css  # same folder as this file


# ---------- PATHS & CONFIG ----------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

st.set_page_config(
    page_title="EcoGranite • Fuel Efficiency Coach",
    page_icon="🚗",
    layout="wide",
)


# ---------- DATA HELPERS ----------

def load_demo_obd() -> pd.DataFrame:
    """Load the cleaned KIT OBD-II dataset as demo data."""
    path = DATA_DIR / "cleaned_kit_obd_combined.csv"
    return pd.read_csv(path)


def load_trip_stats() -> pd.DataFrame:
    """Load pre-computed trip summary stats if available."""
    path = DATA_DIR / "trip_summary_stats.csv"
    return pd.read_csv(path)


def load_granite_feedback() -> pd.DataFrame:
    """
    Load Granite trip feedback from JSON.

    Expected fields (adapt to your actual schema):
      - trip_id / Trip_ID / tripId ...
      - baseline_feedback
      - improved_feedback
    """
    path = DATA_DIR / "granite_trip_feedback.json"

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle possible top-level wrapper {"trips": [...]}
        if isinstance(data, dict):
            for key in ("trips", "records", "results"):
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break

        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to parse Granite feedback JSON: {e}")
        return pd.DataFrame()


def compute_overall_eco_score(row: pd.Series) -> float:
    """
    Scoring tuned to trip_summary_stats.csv structure:
    Trip, Avg_Speed_kmh, Avg_RPM, Avg_Fuel_L/100km,
    HighRPM_LowSpeed_%, Long_Idle_%, Accel_Events, Brake_Events
    """
    score = 100.0

    # fuel efficiency: 0.2–0.5 L/100km in your file -> scale to 0–35 penalty
    if "Avg_Fuel_L/100km" in row:
        fuel = float(row["Avg_Fuel_L/100km"])
        score -= min((fuel - 0.2) * 120, 35)  # more than ~0.5 gets max penalty

    # idling: 0–100% -> up to 30 penalty
    if "Long_Idle_%" in row:
        idle = float(row["Long_Idle_%"])
        score -= min(idle * 0.3, 30)

    # acceleration / braking events -> up to ~35 total
    if "Accel_Events" in row:
        score -= min(float(row["Accel_Events"]) * 0.01, 15)
    if "Brake_Events" in row:
        score -= min(float(row["Brake_Events"]) * 0.01, 20)

    return float(max(0, min(100, score)))


def classify_eco_status(score: float) -> str:
    if score >= 70:
        return "Efficient"
    if score >= 40:
        return "Moderate"
    return "Needs improvement"


# ---------- VISUALS ----------

def eco_gauge(score: float) -> go.Figure:
    """Simple circular gauge for eco score."""
    status = classify_eco_status(score)

    if score < 40:
        bar_color = "#ef4444"
    elif score < 70:
        bar_color = "#f59e0b"
    else:
        bar_color = "#10b981"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={
                "suffix": "",
                "font": {"size": 44, "color": "#f9fafb", "family": "Segoe UI, sans-serif"},
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 0,
                    "tickcolor": "#0f172a",
                },
                "bar": {"color": bar_color, "thickness": 0.3},
                "bgcolor": "rgba(15,23,42,0.9)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "rgba(239, 68, 68, 0.15)"},
                    {"range": [40, 70], "color": "rgba(245, 158, 11, 0.15)"},
                    {"range": [70, 100], "color": "rgba(16, 185, 129, 0.15)"},
                ],
            },
            domain={"x": [0, 1], "y": [0, 1]},
            title={
                "text": f"<b>Eco Score</b><br><span style='font-size:0.8em;color:#94a3b8'>{status}</span>",
                "font": {"size": 16, "color": "#e5e7eb"},
            },
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=0),
        paper_bgcolor="rgba(15,23,42,0.0)",
        plot_bgcolor="rgba(15,23,42,0.0)",
        height=320,
        font=dict(color="#e5e7eb", family="Segoe UI, sans-serif"),
    )
    return fig


def simple_time_series(df: pd.DataFrame, x_col: str, y_col: str, label: str) -> go.Figure:
    """Sleek line chart."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="lines",
            name=label,
            line=dict(width=2),
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=30),
        paper_bgcolor="rgba(15,23,42,0.0)",
        plot_bgcolor="rgba(15,23,42,0.4)",
        font=dict(color="#e5e7eb", family="Segoe UI, sans-serif", size=11),
        xaxis_title="",
        yaxis_title=label,
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148,163,184,0.1)",
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(148,163,184,0.1)",
        ),
        hovermode="x unified",
    )
    return fig


# ---------- UI LAYOUT ----------

FONT_STACK = "Segoe UI, system-ui, -apple-system, BlinkMacSystemFont, sans-serif"


def main() -> None:
    inject_custom_css()

    st.markdown(
        f"""
        <style>
          html, body, .stApp {{
            font-family: {FONT_STACK} !important;
            -webkit-font-smoothing: antialiased;
          }}
          h1, h2, h3, h4 {{
            font-weight: 600;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---------- HEADER ----------
    st.markdown(
        """
        <div style="
            display:flex;
            flex-direction:column;
            gap:4px;
            margin-bottom:18px;
        ">
          <div style="font-size:26px; font-weight:700; color:#f9fafb;">
            EcoGranite
          </div>
          <div style="font-size:13px; color:#9ca3af;">
            Fuel efficiency coach for OBD-II trips
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.header("Trip data")

        uploaded_file = st.file_uploader(
            "Upload OBD-II CSV",
            type=["csv"],
            help="KIT OBD-II data or your own.",
            key="obd_uploader",
        )

        use_demo = st.checkbox(
            "Use demo dataset",
            value=True if not uploaded_file else False,
        )

        if uploaded_file is not None:
            try:
                obd_df = pd.read_csv(uploaded_file)
            except Exception:
                st.error("Could not read uploaded file as CSV.")
                obd_df = pd.DataFrame()
        elif use_demo:
            obd_df = load_demo_obd()
        else:
            obd_df = pd.DataFrame()

        # For debugging: show columns (you can comment this out later)
        st.caption("OBD-II columns:")
        st.code(", ".join(obd_df.columns), language="text")

        trip_stats_df = load_trip_stats()
        granite_df = load_granite_feedback()

        # Try to detect a trip id column
        trip_id_col = None
        for cand in ["Trip", "trip_id", "Trip_ID", "tripId", "trip"]:

            if cand in trip_stats_df.columns:
                trip_id_col = cand
                break

        selected_trip_id = None
        if not trip_stats_df.empty:
            if trip_id_col:
                trip_ids = list(trip_stats_df[trip_id_col].unique())
                selected_trip_id = st.selectbox("Select trip", trip_ids)
            else:
                st.caption("No explicit `trip_id` column found; using row index.")
                selected_trip_id = st.selectbox("Select trip (row index)", trip_stats_df.index)

    if obd_df.empty:
        st.info("Upload a CSV or enable the demo dataset in the sidebar to see the dashboard.")
        return

        # ---------- PER-TRIP CONTEXT ----------
    current_trip_row = None
    if not trip_stats_df.empty:
        if selected_trip_id is not None:
            if trip_id_col:
                matches = trip_stats_df[trip_stats_df[trip_id_col] == selected_trip_id]
                if not matches.empty:
                    current_trip_row = matches.iloc[0]
            else:
                current_trip_row = trip_stats_df.loc[selected_trip_id]
        else:
            current_trip_row = trip_stats_df.iloc[0]

    # ---------- PER-TRIP OBD DATA ----------
    # use only the lines of the selected trip
    trip_obd_df = obd_df.copy()
    if selected_trip_id is not None and "source_file" in trip_obd_df.columns:
        trip_obd_df = trip_obd_df[trip_obd_df["source_file"] == selected_trip_id].copy()

    # Build a datetime axis that uses the date from the trip filename
    x_col = None
    trip_date_str = None
    if isinstance(selected_trip_id, str):
        # filenames like "2017-07-12_Seat_Leon_..."
        trip_date_str = selected_trip_id.split("_")[0]

    if trip_date_str is not None and "Timestamp" in trip_obd_df.columns:
        base_date = pd.to_datetime(trip_date_str, errors="coerce")

        if pd.api.types.is_numeric_dtype(trip_obd_df["Timestamp"]):
            # numeric seconds from start of trip
            trip_obd_df["TripDateTime"] = base_date + pd.to_timedelta(
                trip_obd_df["Timestamp"], unit="s"
            )
        else:
            # assume time-of-day strings; combine with trip date
            trip_obd_df["TripDateTime"] = pd.to_datetime(
                trip_obd_df["Timestamp"].astype(str).apply(
                    lambda t: f"{trip_date_str} {t}"
                ),
                errors="coerce",
            )

        x_col = "TripDateTime"

    # fallback if anything above fails
    if x_col is None:
        for cand in ["Timestamp", "timestamp", "time", "datetime"]:
            if cand in trip_obd_df.columns:
                x_col = cand
                break
        if x_col is None:
            if "index" not in trip_obd_df.columns:
                trip_obd_df = trip_obd_df.reset_index().rename(columns={"index": "index"})
            x_col = "index"


    # Detect speed column
    speed_col = None
    for cand in ["Speed_kmh", "speed_kmh", "Speed", "speed", "SPEED", "vehicle_speed", "vss"]:
        if cand in obd_df.columns:
            speed_col = cand
            break

    # Detect fuel column
    fuel_col = None
    for cand in [
        "fuel_L_s",        # your per-second fuel
        "L_per_100km",     # or pre-computed fuel/100km
        "fuel_rate",
        "FuelRate",
        "FUEL_RATE",
        "fuel_rate_l_h",
        "fuel_consumption",
    ]:
        if cand in obd_df.columns:
            fuel_col = cand
            break

    # ---------- TABS ----------
    dashboard_tab, granite_tab = st.tabs(["Dashboard", "Granite feedback"])

    # ===== TAB 1: DASHBOARD =====
    with dashboard_tab:
        top_left, top_right = st.columns([1.1, 1])

        with top_left:
            st.subheader("Eco score")
            if current_trip_row is not None:
                eco_score = compute_overall_eco_score(current_trip_row)
            else:
                eco_score = 72.0
            fig = eco_gauge(eco_score)
            st.plotly_chart(fig, use_container_width=True)

        with top_right:
            st.subheader("Trip snapshot")

            if current_trip_row is not None:
                # Columns based on trip_summary_stats.csv
                metric_defs = [
                    ("Avg speed", "Avg_Speed_kmh", "km/h", 1),
                    ("Avg RPM", "Avg_RPM", "", 0),
                    ("Fuel (avg)", "Avg_Fuel_L/100km", "L/100km", 2),
                    ("High RPM @ low speed", "HighRPM_LowSpeed_%", "%", 1),
                    ("Long idle", "Long_Idle_%", "%", 1),
                    ("Accel events", "Accel_Events", "", 0),
                    ("Brake events", "Brake_Events", "", 0),
                ]

                cols = st.columns(3)
                i = 0
                for label, col_name, unit, decimals in metric_defs:
                    if col_name in current_trip_row.index:
                        val = current_trip_row[col_name]
                        if unit:
                            display_val = f"{val:.{decimals}f} {unit}"
                        else:
                            # counts like events / RPM
                            display_val = f"{val:.{decimals}f}"
                        with cols[i % 3]:
                            st.metric(label, display_val)
                        i += 1
            else:
                st.caption("No trip stats available yet.")


        st.markdown("---")

        chart_left, chart_right = st.columns(2)

        with chart_left:
            st.subheader("Speed profile")
            if speed_col:
                fig_speed = simple_time_series(trip_obd_df, x_col, speed_col, "Speed")
                st.plotly_chart(fig_speed, use_container_width=True, key="speed_chart")
            else:
                st.caption("Speed column not found in this dataset.")

        with chart_right:
            st.subheader("Fuel consumption")
            if fuel_col:
                fig_fuel = simple_time_series(trip_obd_df, x_col, fuel_col, "Fuel rate")
                st.plotly_chart(fig_fuel, use_container_width=True, key="fuel_chart")
            else:
                st.caption("Fuel rate column not found in this dataset.")


    # ===== TAB 2: GRANITE FEEDBACK =====
    with granite_tab:
        st.subheader("IBM Granite coaching")

        granite_df = load_granite_feedback()
        if granite_df.empty:
            st.info("Granite feedback will appear here once notebooks export `granite_trip_feedback.json`.")
        else:
            trip_feedback_df = granite_df.copy()

            # detect trip id column for Granite file (your file uses "Trip")
            granite_trip_id_col = None
            for cand in ["Trip", "trip_id", "Trip_ID", "tripId", "trip"]:
                if cand in trip_feedback_df.columns:
                    granite_trip_id_col = cand
                    break

            if selected_trip_id is not None and granite_trip_id_col:
                trip_feedback_df = trip_feedback_df[trip_feedback_df[granite_trip_id_col] == selected_trip_id]

            if trip_feedback_df.empty:
                st.caption("No Granite feedback for this trip yet.")
            else:
                row = trip_feedback_df.iloc[0]

                # your schema: Trip, prompt, feedback
                prompt_text = row.get("prompt", "(no prompt available)")
                feedback_text = row.get("feedback", "(no feedback available)")

                cols_fb = st.columns(2)
                with cols_fb[0]:
                    st.markdown("**Granite prompt (trip summary)**")
                    st.markdown(
                        f"""
                        <div style="
                            background: rgba(148,163,184,0.07);
                            border-left: 3px solid #9ca3af;
                            padding: 14px;
                            border-radius: 6px;
                            font-size:13px;
                            white-space:pre-wrap;
                        ">
                        {prompt_text}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with cols_fb[1]:
                    st.markdown("**Granite coaching (AI response)**")
                    st.markdown(
                        f"""
                        <div style="
                            background: rgba(34,197,94,0.07);
                            border-left: 3px solid #10b981;
                            padding: 14px;
                            border-radius: 6px;
                            font-size:13px;
                            white-space:pre-wrap;
                        ">
                        {feedback_text}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


if __name__ == "__main__":
    main()

