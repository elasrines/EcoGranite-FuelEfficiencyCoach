# src/dashboard_app.py

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

def build_trip_insights(row: pd.Series) -> list[dict]:
    """
    Return a list of insight dicts:
    { "severity": "bad" | "warn" | "good", "title": str, "text": str }
    based on trip_summary_stats metrics.
    """
    insights = []

    fuel = row.get("Avg_Fuel_L/100km")
    idle = row.get("Long_Idle_%")
    high_rpm = row.get("HighRPM_LowSpeed_%")
    accel = row.get("Accel_Events")
    brake = row.get("Brake_Events")

    # Fuel usage
    if pd.notna(fuel):
        # ≤ 0.30 → efficient, 0.30–0.40 → moderate, ≥ 0.40 → high
        if fuel >= 0.40:
            insights.append({
                "severity": "bad",
                "title": "Fuel usage high",
                "text": f"Average fuel consumption is {fuel:.2f} L/100km – consider smoother acceleration and lower RPM where possible."
            })
        elif fuel <= 0.30:
            insights.append({
                "severity": "good",
                "title": "Fuel usage efficient",
                "text": f"Average fuel consumption is only {fuel:.2f} L/100km – this is efficient for this vehicle."
            })
        else:
            insights.append({
                "severity": "warn",
                "title": "Fuel usage moderate",
                "text": f"Fuel consumption is {fuel:.2f} L/100km – acceptable, but there is room to reduce it with gentler throttle input."
            })


    # Idling
    if pd.notna(idle):
        if idle >= 50:
            insights.append({
                "severity": "bad",
                "title": "Idle time very high",
                "text": f"Long idle time is {idle:.1f}% of the trip – switching off the engine during long stops would reduce wasted fuel."
            })
        elif idle >= 20:
            insights.append({
                "severity": "warn",
                "title": "Idle time noticeable",
                "text": f"Long idle time is {idle:.1f}% – some of this could likely be avoided."
            })
        else:
            insights.append({
                "severity": "good",
                "title": "Idle time under control",
                "text": f"Long idle time is only {idle:.1f}% – good anticipation of stops and traffic."
            })

    # High RPM at low speed
    if pd.notna(high_rpm):
        # ≥ 0.10% → clearly bad, 0.02–0.10% → occasional (warn), < 0.02% → efficient
        if high_rpm >= 0.10:
            insights.append({
                "severity": "bad",
                "title": "High RPM at low speed",
                "text": f"{high_rpm:.2f}% of the trip was spent at high RPM and low speed – upshifting earlier would reduce fuel use."
            })
        elif high_rpm >= 0.02:
            insights.append({
                "severity": "warn",
                "title": "Occasional high RPM",
                "text": f"{high_rpm:.2f}% of the trip had high RPM at low speed – mostly fine, but there’s still room to upshift a bit earlier."
            })
        else:
            insights.append({
                "severity": "good",
                "title": "RPM usage efficient",
                "text": "Very little time was spent at high RPM and low speed – gear selection looks efficient."
            })


    # Aggressive events (accel + brake) – simple heuristic
    if pd.notna(accel) and pd.notna(brake):
        total_events = float(accel) + float(brake)
        if total_events >= 800:
            insights.append({
                "severity": "bad",
                "title": "Many acceleration/braking events",
                "text": f"There were {int(accel)} acceleration and {int(brake)} braking events – smoother, more anticipatory driving would help."
            })
        elif total_events >= 400:
            insights.append({
                "severity": "warn",
                "title": "Frequent speed changes",
                "text": f"{int(accel)} acceleration and {int(brake)} braking events – typical for heavy traffic, but still a chance to smooth things out."
            })
        else:
            insights.append({
                "severity": "good",
                "title": "Smooth speed profile",
                "text": f"Only {int(accel)} acceleration and {int(brake)} braking events – indicates generally smooth driving."
            })

    return insights

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
    """Full-size sleek line chart."""
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
        height=280,
    )
    return fig


def compact_time_series(df: pd.DataFrame, x_col: str, y_col: str, label: str) -> go.Figure:
    """Small sparkline-style chart for trip traces."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="lines",
            name=label,
            line=dict(width=1.5),
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=18, b=12),
        paper_bgcolor="rgba(15,23,42,0.0)",
        plot_bgcolor="rgba(15,23,42,0.45)",
        font=dict(color="#e5e7eb", family="Segoe UI, sans-serif", size=9),
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
        ),
        showlegend=False,
        height=130,
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

        st.caption("OBD-II columns:")
        st.code(", ".join(obd_df.columns), language="text")

        trip_stats_df = load_trip_stats()
        granite_df = load_granite_feedback()

        # Detect trip id column
        trip_id_col = None
        for cand in ["Trip", "trip_id", "Trip_ID", "tripId", "trip"]:
            if cand in trip_stats_df.columns:
                trip_id_col = cand
                break

        # ---- Trip filters ----
        st.subheader("Trip filters")
        filter_mode = st.radio(
            "Highlight trips by",
            ["All trips", "High idle", "High RPM", "High fuel use"],
            index=0,
        )

        filtered_trip_stats = trip_stats_df.copy()
        filter_caption = ""

        if not trip_stats_df.empty and trip_id_col:
            # High idle → align with insight "Idle time very high" (>= 50%)
            if filter_mode == "High idle" and "Long_Idle_%" in trip_stats_df.columns:
                idle_metric = trip_stats_df["Long_Idle_%"].fillna(0.0)
                filtered_trip_stats = trip_stats_df[idle_metric >= 50.0]
                filter_caption = "Trips with idle time ≥ 50% (very high idle)."

            # High RPM → align with insight thresholds: >0.1% is at least "occasional high RPM"
            elif filter_mode == "High RPM" and "HighRPM_LowSpeed_%" in trip_stats_df.columns:
                rpm_metric = trip_stats_df["HighRPM_LowSpeed_%"].fillna(0.0)
                # Align with insights: include all trips that are at least "warn"
                # i.e. HighRPM_LowSpeed_% ≥ 0.02%
                filtered_trip_stats = trip_stats_df[rpm_metric >= 0.02]
                filter_caption = "Trips with ≥ 0.02% time at high RPM and low speed."

            # High fuel → align with insight "Fuel usage high" (>= 0.40 L/100km)
            elif filter_mode == "High fuel use" and "Avg_Fuel_L/100km" in trip_stats_df.columns:
                fuel_metric = trip_stats_df["Avg_Fuel_L/100km"].fillna(0.0)
                filtered_trip_stats = trip_stats_df[fuel_metric >= 0.40]
                filter_caption = "Trips with avg fuel ≥ 0.40 L/100km (high usage)."


        selected_trip_id = None
        if not filtered_trip_stats.empty:
            if trip_id_col:
                trip_ids = list(filtered_trip_stats[trip_id_col].unique())
                selected_trip_id = st.selectbox("Select trip", trip_ids)
                if filter_caption:
                    st.caption(filter_caption)
            else:
                st.caption("No explicit `trip_id` column found; using row index.")
                selected_trip_id = st.selectbox("Select trip (row index)", filtered_trip_stats.index)
        else:
            st.caption("No trips available for this filter.")

    if obd_df.empty:
        st.info("Upload a CSV or enable the demo dataset in the sidebar to see the dashboard.")
        return

    # ---------- PER-TRIP CONTEXT ----------
    current_trip_row = None
    if not filtered_trip_stats.empty:
        if selected_trip_id is not None:
            if trip_id_col:
                matches = filtered_trip_stats[filtered_trip_stats[trip_id_col] == selected_trip_id]
                if not matches.empty:
                    current_trip_row = matches.iloc[0]
            else:
                current_trip_row = filtered_trip_stats.loc[selected_trip_id]
        else:
            current_trip_row = filtered_trip_stats.iloc[0]

    # ---------- PER-TRIP OBD DATA ----------
    trip_obd_df = obd_df.copy()
    if selected_trip_id is not None and "source_file" in trip_obd_df.columns:
        trip_obd_df = trip_obd_df[trip_obd_df["source_file"] == selected_trip_id].copy()

    # Build a datetime axis that uses the date from the trip filename
    x_col = None
    trip_date_str = None
    if isinstance(selected_trip_id, str):
        trip_date_str = selected_trip_id.split("_")[0]

    if trip_date_str is not None and "Timestamp" in trip_obd_df.columns:
        base_date = pd.to_datetime(trip_date_str, errors="coerce")

        if pd.api.types.is_numeric_dtype(trip_obd_df["Timestamp"]):
            trip_obd_df["TripDateTime"] = base_date + pd.to_timedelta(
                trip_obd_df["Timestamp"], unit="s"
            )
        else:
            trip_obd_df["TripDateTime"] = pd.to_datetime(
                trip_obd_df["Timestamp"].astype(str).apply(
                    lambda t: f"{trip_date_str} {t}"
                ),
                errors="coerce",
            )

        x_col = "TripDateTime"

    if x_col is None:
        for cand in ["Timestamp", "timestamp", "time", "datetime"]:
            if cand in trip_obd_df.columns:
                x_col = cand
                break
        if x_col is None:
            if "index" not in trip_obd_df.columns:
                trip_obd_df = trip_obd_df.reset_index().rename(columns={"index": "index"})
            x_col = "index"

    # Detect columns in OBD data
    speed_col = None
    for cand in ["Speed_kmh", "speed_kmh", "Speed", "speed", "SPEED", "vehicle_speed", "vss"]:
        if cand in trip_obd_df.columns:
            speed_col = cand
            break

    fuel_col = None
    for cand in [
        "fuel_L_s",
        "L_per_100km",
        "fuel_rate",
        "FuelRate",
        "FUEL_RATE",
        "fuel_rate_l_h",
        "fuel_consumption",
    ]:
        if cand in trip_obd_df.columns:
            fuel_col = cand
            break

    rpm_col = None
    for cand in ["RPM", "engine_rpm", "EngineRPM"]:
        if cand in trip_obd_df.columns:
            rpm_col = cand
            break

    # ---------- TABS ----------
    dashboard_tab, granite_tab = st.tabs(["Dashboard", "Granite feedback"])

    # ===== TAB 1: DASHBOARD =====
    with dashboard_tab:

        # --- TOP ROW: Trip snapshot (left) + Eco score (right) ---
        top_left, top_right = st.columns([1.2, 1])

        # LEFT → Trip snapshot
        with top_left:
            st.subheader("Trip snapshot")

            if current_trip_row is not None:
                metric_defs = [
                    ("Avg speed", "Avg_Speed_kmh", "km/h", 1),
                    ("Avg RPM", "Avg_RPM", "", 0),
                    ("Fuel (avg)", "Avg_Fuel_L/100km", "L/100km", 2),
                    ("High RPM @ low speed", "HighRPM_LowSpeed_%", "%", 2),
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
                            display_val = f"{val:.{decimals}f}"
                        with cols[i % 3]:
                            st.metric(label, display_val)
                        i += 1
            else:
                st.caption("No trip stats available yet.")

        # RIGHT → Eco score
        with top_right:
            st.subheader("Trip eco score")

            if current_trip_row is not None:
                eco_score = compute_overall_eco_score(current_trip_row)
            else:
                eco_score = 72.0

            fig = eco_gauge(eco_score)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        # --- SECOND ROW: Driving insights (full width) ---
        st.subheader("Driving insights")

        if current_trip_row is None:
            st.caption("Select a trip to see key positives and pain points.")
        else:
            insights = build_trip_insights(current_trip_row)
            if not insights:
                st.caption("No insights available for this trip.")
            else:
                for ins in insights:
                    sev = ins["severity"]
                    if sev == "bad":
                        border = "#ef4444"
                        bg = "rgba(239,68,68,0.08)"
                    elif sev == "warn":
                        border = "#f59e0b"
                        bg = "rgba(245,158,11,0.08)"
                    else:
                        border = "#10b981"
                        bg = "rgba(16,185,129,0.08)"

                    st.markdown(
                        f"""
                        <div style="
                            background:{bg};
                            border-left:3px solid {border};
                            padding:10px 12px;
                            border-radius:8px;
                            margin-bottom:8px;
                            font-size:13px;
                        ">
                        <div style="font-weight:600; margin-bottom:2px;">
                            {ins['title']}
                        </div>
                        <div style="color:#e5e7eb;">
                            {ins['text']}
                        </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.markdown("---")
        

        # ===== SPEED PROFILE =====
        st.subheader("Speed profile")
        if speed_col:
            fig_speed = simple_time_series(trip_obd_df, x_col, speed_col, "Speed")
            st.plotly_chart(fig_speed, use_container_width=True, key="speed_chart")
        else:
            st.caption("Speed column not found in this dataset.")

        st.markdown("---")

        # ===== RPM PROFILE =====
        st.subheader("RPM profile")
        if rpm_col:
            fig_rpm = simple_time_series(trip_obd_df, x_col, rpm_col, "RPM")
            st.plotly_chart(fig_rpm, use_container_width=True, key="rpm_chart")
        else:
            st.caption("RPM column not found in this dataset.")

        st.markdown("---")

        # ===== FUEL CONSUMPTION =====
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
