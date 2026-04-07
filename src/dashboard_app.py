# src/dashboard_app.py

from __future__ import annotations

from pathlib import Path
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import requests


# =========================
# PATHS & PAGE CONFIG
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

st.set_page_config(
    page_title="EcoGranite • Fuel Efficiency Coach",
    page_icon="🚗",
    layout="wide",
)


# =========================
# CSS (single injection)
# =========================

def inject_css(active_page: str) -> None:
    """
    One place for all styling, including active sidebar nav button styling.
    Uses Streamlit's `st-key-<key>` wrapper to target the active button.
    """
    active_slug = slugify(active_page)

    st.markdown(
        f"""
<style>
:root {{
  --eg-bg: #f6f7f9;
  --eg-card: #ffffff;
  --eg-text: #0f172a;
  --eg-muted: rgba(15,23,42,0.65);
  --eg-border: rgba(15,23,42,0.10);
  --eg-accent: rgba(239,68,68,0.14);
  --eg-accent-border: rgba(239,68,68,0.28);
}}

/* App base */
.stApp {{
  background: var(--eg-bg) !important;
  color: var(--eg-text) !important;
}}
.stApp, .stApp * {{
  color: var(--eg-text);
}}

/* Sidebar + header */
section[data-testid="stSidebar"] {{
  background: var(--eg-card) !important;
  border-right: 1px solid var(--eg-border) !important;
}}
header[data-testid="stHeader"] {{
  background: var(--eg-card) !important;
  border-bottom: 1px solid var(--eg-border) !important;
}}

/* Links inside sidebar */
section[data-testid="stSidebar"] a {{
  color: rgba(15,23,42,0.7);
  text-decoration: none;
  font-size: 13px;
}}
section[data-testid="stSidebar"] a:hover {{
  color: #0f172a;
  text-decoration: underline;
}}

/* Sidebar input containers */
section[data-testid="stSidebar"] [data-testid="stFileUploader"],
section[data-testid="stSidebar"] [data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-testid="stRadio"],
section[data-testid="stSidebar"] [data-testid="stCheckbox"] {{
  background: var(--eg-card) !important;
  border: 1px solid rgba(15,23,42,0.08) !important;
  border-radius: 14px !important;
  padding: 10px !important;
  box-shadow: 0 10px 25px rgba(15,23,42,0.06) !important;
}}

/* Select trigger */
section[data-testid="stSidebar"] [data-baseweb="select"] div[role="combobox"] {{
  background: var(--eg-card) !important;
  border: 1px solid rgba(15,23,42,0.12) !important;
  border-radius: 12px !important;
  color: var(--eg-text) !important;
}}

/* Dropdown menu surface */
div[role="listbox"] {{
  background: var(--eg-card) !important;
  color: var(--eg-text) !important;
  border: 1px solid var(--eg-border) !important;
  border-radius: 12px !important;
  box-shadow: 0 18px 40px rgba(15,23,42,0.12) !important;
}}
div[role="option"] {{
  background: var(--eg-card) !important;
  color: var(--eg-text) !important;
}}
div[role="option"]:hover {{
  background: rgba(15,23,42,0.05) !important;
}}

/* Code blocks */
pre, code, .stCodeBlock, .stCodeBlock * {{
  color: var(--eg-text) !important;
  background: var(--eg-card) !important;
}}

/* Metrics: reduce sizes */
[data-testid="stMetric"] {{ padding: 6px 0 !important; }}
[data-testid="stMetricLabel"] {{
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  color: var(--eg-muted) !important;
  line-height: 1.1 !important;
}}
[data-testid="stMetricValue"] {{
  font-size: 1.05rem !important;
  font-weight: 650 !important;
  color: var(--eg-text) !important;
  line-height: 1.15 !important;
}}

/* =========================
   SIDEBAR NAV BUTTONS
   ========================= */

/* Default nav buttons */
section[data-testid="stSidebar"] .stButton > button {{
  background: #f3f4f6 !important;
  color: #0f172a !important;
  border: 1px solid rgba(15,23,42,0.12) !important;
  border-radius: 14px !important;
  padding: 12px 14px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
  background: #e5e7eb !important;
}}

/* ACTIVE nav button (only) */
section[data-testid="stSidebar"] .st-key-nav_{active_slug} .stButton > button {{
  background: #9ca3af !important;
  font-weight: 700 !important;
  box-shadow: inset 0 0 0 1px rgba(15,23,42,0.22) !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def slugify(text: str) -> str:
    return text.strip().lower().replace(" ", "_")


# =========================
# DATA HELPERS
# =========================

def load_demo_obd() -> pd.DataFrame:
    path = DATA_DIR / "demo_cleaned_kit_obd_combined.csv"
    if not path.exists():
        st.warning("Demo OBD dataset not found. Please upload a CSV instead.")
        return pd.DataFrame()
    return pd.read_csv(path)


def load_trip_stats() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "trip_summary_stats.csv")


def normalize_uploaded_obd_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize common uploaded/raw KIT-style column names to the names used by the dashboard.
    """
    if df.empty:
        return df

    df = df.copy()

    rename_map = {
        "engine_rpm_[rpm]": "RPM",
        "vehicle_speed_sensor_[km/h]": "Speed_kmh",
        "air_flow_rate_from_mass_flow_sensor_[g/s]": "MAF_g_s",
        "time": "Timestamp",
        "gps_time": "Timestamp",
        "source": "source_file",
        "trip": "source_file",
        "trip_id": "source_file",
    }

    existing_map = {old: new for old, new in rename_map.items() if old in df.columns and new not in df.columns}
    if existing_map:
        df = df.rename(columns=existing_map)

    return df


def build_trip_stats_from_obd(obd_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a lightweight trip summary directly from the uploaded OBD dataframe,
    so the trip dropdown and dashboard reflect uploaded files instead of demo stats.
    """
    if obd_df.empty:
        return pd.DataFrame()

    df = normalize_uploaded_obd_columns(obd_df)

    if "source_file" not in df.columns:
        df = df.copy()
        df["source_file"] = "uploaded_trip"

    rpm_col = find_first_col(df, ["RPM", "engine_rpm", "EngineRPM"])
    speed_col = find_first_col(df, ["Speed_kmh", "speed_kmh", "Speed", "speed", "SPEED", "vehicle_speed", "vss"])
    fuel_col = find_first_col(
        df,
        ["Avg_Fuel_L/100km", "L_per_100km", "fuel_L_s", "fuel_rate", "FuelRate", "FUEL_RATE", "fuel_rate_l_h", "fuel_consumption"],
    )

    rows: list[dict] = []

    for trip_id, trip_df in df.groupby("source_file", dropna=False):
        trip_df = trip_df.copy()

        row: dict = {"Trip": trip_id}

        # Avg speed
        if speed_col and speed_col in trip_df.columns:
            row["Avg_Speed_kmh"] = pd.to_numeric(trip_df[speed_col], errors="coerce").mean()
        else:
            row["Avg_Speed_kmh"] = pd.NA

        # Avg RPM
        if rpm_col and rpm_col in trip_df.columns:
            rpm_series = pd.to_numeric(trip_df[rpm_col], errors="coerce")
            row["Avg_RPM"] = rpm_series.mean()
        else:
            rpm_series = pd.Series(dtype=float)
            row["Avg_RPM"] = pd.NA

        # Fuel
        if fuel_col and fuel_col in trip_df.columns:
            fuel_series = pd.to_numeric(trip_df[fuel_col], errors="coerce")
            row["Avg_Fuel_L/100km"] = fuel_series.mean()
        else:
            fuel_series = pd.Series(dtype=float)
            row["Avg_Fuel_L/100km"] = pd.NA

        # High RPM at low speed %
        if not rpm_series.empty and speed_col and speed_col in trip_df.columns:
            speed_series = pd.to_numeric(trip_df[speed_col], errors="coerce")
            valid_mask = rpm_series.notna() & speed_series.notna()
            if valid_mask.any():
                inefficient_mask = (rpm_series > 3000) & (speed_series < 30)
                row["HighRPM_LowSpeed_%"] = float(inefficient_mask[valid_mask].mean() * 100)
            else:
                row["HighRPM_LowSpeed_%"] = pd.NA
        else:
            row["HighRPM_LowSpeed_%"] = pd.NA

        # Long idle time %
        if speed_col and speed_col in trip_df.columns:
            speed_series = pd.to_numeric(trip_df[speed_col], errors="coerce")
            valid_speed = speed_series.notna()
            if valid_speed.any():
                idle_mask = speed_series <= 1
                row["Long_Idle_Time_%"] = float(idle_mask[valid_speed].mean() * 100)
            else:
                row["Long_Idle_Time_%"] = pd.NA
        else:
            row["Long_Idle_Time_%"] = pd.NA

        # Approx acceleration / braking event counts
        if speed_col and speed_col in trip_df.columns:
            speed_series = pd.to_numeric(trip_df[speed_col], errors="coerce").reset_index(drop=True)
            delta = speed_series.diff()

            row["Accel_Events"] = int((delta > 8).sum()) if not delta.empty else 0
            row["Brake_Events"] = int((delta < -8).sum()) if not delta.empty else 0
        else:
            row["Accel_Events"] = pd.NA
            row["Brake_Events"] = pd.NA

        rows.append(row)

    trip_stats_df = pd.DataFrame(rows)

    if not trip_stats_df.empty:
        trip_stats_df["Eco_Score"] = trip_stats_df.apply(compute_overall_eco_score, axis=1)

    return trip_stats_df


def load_granite_feedback() -> pd.DataFrame:
    path = DATA_DIR / "granite_trip_feedback.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            for key in ("trips", "records", "results"):
                if isinstance(data.get(key), list):
                    data = data[key]
                    break

        return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to parse Granite feedback JSON: {e}")
        return pd.DataFrame()

WATSONX_CHAT_URL = "https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-05-29"
WATSONX_PROJECT_ID = "852aeb95-062b-40a1-b2fa-da7a22b9dba4"
WATSONX_MODEL_ID = "ibm/granite-4-h-small"


def safe_num(value, decimals: int = 2, fallback: str = "N/A") -> str:
    if pd.isna(value):
        return fallback
    return f"{float(value):.{decimals}f}"


def safe_int(value, fallback: str = "N/A") -> str:
    if pd.isna(value):
        return fallback
    return str(int(value))


def get_iam_access_token(api_key: str) -> str:
    iam_url = "https://iam.cloud.ibm.com/identity/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key,
    }

    r = requests.post(iam_url, headers=headers, data=data, timeout=30)
    if r.status_code != 200:
        raise Exception(f"IAM token error {r.status_code}: {r.text}")

    return r.json()["access_token"]


def build_live_granite_prompt(row: pd.Series) -> str:
    eco_score = compute_overall_eco_score(row)
    trip_label = classify_eco_status(eco_score)

    penalties = compute_penalties(row)
    ranked = sorted(penalties.items(), key=lambda kv: kv[1], reverse=True)

    main_issue = ranked[0][0] if len(ranked) >= 1 else "No major issue detected"
    second_issue = ranked[1][0] if len(ranked) >= 2 else "No second major issue detected"

    insights = build_trip_insights(row)
    good_items = [ins["title"] for ins in insights if ins["severity"] == "good"]
    improve_items = [ins["title"] for ins in insights if ins["severity"] in ("warn", "bad")]

    while len(good_items) < 2:
        good_items.append("No additional strong positive detected")
    while len(improve_items) < 2:
        improve_items.append("No additional major improvement area detected")

    return f"""
You are writing coaching text for the EcoGranite dashboard.

Important rules:
- Use the dashboard assessment below as the source of truth.
- Do not contradict the provided issues or strengths.
- Do not say fuel use is good if the dashboard says fuel use is bad.
- Use the exact metric values provided.
- Return plain text only.
- Do not use markdown.
- Do not use asterisks.
- Leave one blank line between sections.
- Use exactly these section headers:
Overview:
Coaching Suggestions:
Key Takeaway:

Dashboard assessment:
- Eco score: {eco_score:.1f}
- Trip classification: {trip_label}
- Main issue: {main_issue}
- Second issue: {second_issue}

Trip metrics:
- Average speed: {safe_num(row.get('Avg_Speed_kmh'), 1)} km/h
- Average RPM: {safe_num(row.get('Avg_RPM'), 0)}
- Average fuel consumption: {safe_num(row.get('Avg_Fuel_L/100km'), 2)} L/100km
- High RPM at low speed events: {safe_num(row.get('HighRPM_LowSpeed_%'), 2)}%
- Long idling: {safe_num(row.get('Long_Idle_Time_%'), 2)}%
- Acceleration events: {safe_int(row.get('Accel_Events'))}
- Braking events: {safe_int(row.get('Brake_Events'))}

What went well:
- {good_items[0]}
- {good_items[1]}

What could improve:
- {improve_items[0]}
- {improve_items[1]}

Write:
1. An Overview of 3 to 4 sentences.
2. 4 bullet coaching suggestions.
3. A Key Takeaway of 1 sentence.

Do not invent new problems.
Do not change the meaning of the dashboard assessment.
""".strip()


def call_granite(prompt_text: str, access_token: str, temperature: float = 0.2, max_tokens: int = 350) -> str:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    body = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are EcoGranite, a fuel-efficiency driving coach. "
                    "Give supportive, practical eco-driving feedback."
                ),
            },
            {
                "role": "user",
                "content": prompt_text,
            },
        ],
        "project_id": WATSONX_PROJECT_ID,
        "model_id": WATSONX_MODEL_ID,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    r = requests.post(WATSONX_CHAT_URL, json=body, headers=headers, timeout=60)
    if r.status_code != 200:
        raise Exception(f"Granite error {r.status_code}: {r.text}")

    return r.json()["choices"][0]["message"]["content"]


@st.cache_data(show_spinner=False)
def generate_live_granite_feedback(
    trip_id: str,
    prompt_text: str,
    temperature: float = 0.2,
) -> dict:
    api_key = os.getenv("WATSONX_API_KEY")
    if not api_key:
        raise ValueError("WATSONX_API_KEY not found in environment.")

    access_token = get_iam_access_token(api_key)
    feedback = call_granite(prompt_text, access_token, temperature=temperature)

    return {
        "Trip": trip_id,
        "prompt": prompt_text,
        "feedback": feedback,
        "temperature": temperature,
        "model_id": WATSONX_MODEL_ID,
        "source": "live",
    }

# =========================
# SCORING & INSIGHTS
# =========================

def compute_overall_eco_score(row: pd.Series) -> float:
    score = 100.0

    fuel = row.get("Avg_Fuel_L/100km")
    if pd.notna(fuel):
        score -= min((float(fuel) - 0.2) * 120, 35)

    idle = row.get("Long_Idle_Time_%")
    if pd.notna(idle):
        score -= min(float(idle) * 0.5, 30)

    accel = row.get("Accel_Events")
    if pd.notna(accel):
        score -= min(float(accel) * 0.01, 15)

    brake = row.get("Brake_Events")
    if pd.notna(brake):
        score -= min(float(brake) * 0.01, 20)

    return float(max(0, min(100, score)))


def classify_eco_status(score: float) -> str:
    if score >= 70:
        return "Efficient"
    if score >= 40:
        return "Moderate"
    return "in need of improvement"


def build_trip_insights(row: pd.Series) -> list[dict]:
    insights: list[dict] = []

    fuel = row.get("Avg_Fuel_L/100km")
    idle = row.get("Long_Idle_Time_%")
    high_rpm = row.get("HighRPM_LowSpeed_%")
    accel = row.get("Accel_Events")
    brake = row.get("Brake_Events")

    if pd.notna(fuel):
        if fuel >= 0.40:
            insights.append(
                {
                    "severity": "bad",
                    "title": "Fuel usage high",
                    "text": f"Average fuel consumption is {fuel:.2f} L/100km – consider smoother acceleration and lower RPM where possible.",
                }
            )
        elif fuel <= 0.30:
            insights.append(
                {
                    "severity": "good",
                    "title": "Fuel usage efficient",
                    "text": f"Average fuel consumption is only {fuel:.2f} L/100km – this is efficient for this vehicle.",
                }
            )
        else:
            insights.append(
                {
                    "severity": "warn",
                    "title": "Fuel usage moderate",
                    "text": f"Fuel consumption is {fuel:.2f} L/100km – acceptable, but there is room to reduce it with gentler throttle input.",
                }
            )

    if pd.notna(idle):
        if idle >= 50:
            insights.append(
                {
                    "severity": "bad",
                    "title": "Idle time very high",
                    "text": f"Long idle time is {idle:.1f}% of the trip – switching off the engine during long stops would reduce wasted fuel.",
                }
            )
        elif idle >= 20:
            insights.append(
                {
                    "severity": "warn",
                    "title": "Idle time noticeable",
                    "text": f"Long idle time is {idle:.1f}% – some of this could likely be avoided.",
                }
            )
        else:
            insights.append(
                {
                    "severity": "good",
                    "title": "Idle time under control",
                    "text": f"Long idle time is only {idle:.1f}% – good anticipation of stops and traffic.",
                }
            )

    if pd.notna(high_rpm):
        if high_rpm >= 5.0:
            insights.append(
                {
                    "severity": "bad",
                    "title": "High RPM at low speed",
                    "text": f"{high_rpm:.1f}% of the trip was spent at high RPM and low speed – this significantly increases fuel use.",
                }
            )
        elif high_rpm >= 2.0:
            insights.append(
                {
                    "severity": "warn",
                    "title": "Occasional high RPM",
                    "text": f"{high_rpm:.1f}% of the trip had high RPM at low speed – upshifting slightly earlier would help.",
                }
            )
        else:
            insights.append(
                {
                    "severity": "good",
                    "title": "RPM usage efficient",
                    "text": "Very little time was spent at high RPM and low speed – gear selection looks efficient.",
                }
            )


    if pd.notna(accel) and pd.notna(brake):
        total = float(accel) + float(brake)
        if total >= 800:
            insights.append(
                {
                    "severity": "bad",
                    "title": "Many acceleration/braking events",
                    "text": f"There were {int(accel)} acceleration and {int(brake)} braking events – smoother, more anticipatory driving would help.",
                }
            )
        elif total >= 400:
            insights.append(
                {
                    "severity": "warn",
                    "title": "Frequent speed changes",
                    "text": f"{int(accel)} acceleration and {int(brake)} braking events – typical for heavy traffic, but still a chance to smooth things out.",
                }
            )
        else:
            insights.append(
                {
                    "severity": "good",
                    "title": "Smooth speed profile",
                    "text": f"Only {int(accel)} acceleration and {int(brake)} braking events – indicates generally smooth driving.",
                }
            )

    return insights

def compute_penalties(row: pd.Series) -> dict[str, float]:
    """
    Return each component's penalty in points (same logic as compute_overall_eco_score).
    """
    penalties: dict[str, float] = {}

    # Fuel penalty (max 35)
    fuel = row.get("Avg_Fuel_L/100km")
    if pd.notna(fuel):
        fuel_pen = min((float(fuel) - 0.2) * 120, 35)
        penalties["Fuel use"] = max(0.0, float(fuel_pen))

    # Idle penalty (max 30)
    idle = row.get("Long_Idle_Time_%")
    if pd.notna(idle):
        idle_pen = min(float(idle) * 0.3, 30)
        penalties["Idling"] = max(0.0, float(idle_pen))

    # Accel penalty (max 15)
    accel = row.get("Accel_Events")
    if pd.notna(accel):
        accel_pen = min(float(accel) * 0.01, 15)
        penalties["Acceleration events"] = max(0.0, float(accel_pen))

    # Brake penalty (max 20)
    brake = row.get("Brake_Events")
    if pd.notna(brake):
        brake_pen = min(float(brake) * 0.01, 20)
        penalties["Braking events"] = max(0.0, float(brake_pen))

    return penalties


def top_drivers_text(penalties: dict[str, float], *, k: int = 2) -> list[str]:
    """
    Returns lines like:
    "Main issue: Idling (−18 pts)"
    "Second issue: Braking events (−9 pts)"
    """
    if not penalties:
        return []

    ranked = sorted(penalties.items(), key=lambda kv: kv[1], reverse=True)

    labels = ["Main issue", "Second issue", "Third issue"]
    lines: list[str] = []

    for i, (name, pts) in enumerate(ranked[:k]):
        tag = labels[i] if i < len(labels) else f"Issue #{i+1}"
        lines.append(f"{tag}: {name} (−{pts:.0f} pts)")

    return lines

def render_story_drivers_card(lines: list[str]) -> None:
    if not lines:
        return

    bullets = "".join(f"<li style='margin-bottom:6px;'>{ln}</li>" for ln in lines)

    st.markdown(
        f"""
        <div style="
            background:#ffffff;
            border:1px solid rgba(15,23,42,0.10);
            padding:12px 14px;
            border-radius:12px;
            margin-bottom:12px;
            font-size:14px;
        ">
          <div style="font-weight:650; margin-bottom:8px;">What drove your score</div>
          <ul style="margin:0; padding-left:18px;">
            {bullets}
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


    
# =========================
# PLOTLY
# =========================

def apply_plotly_theme(fig: go.Figure) -> go.Figure:
    dark = "#0f172a"
    grid = "rgba(15,23,42,0.10)"

    fig.update_layout(
        margin=dict(l=8, r=8, t=30, b=10),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color=dark, family="Segoe UI, sans-serif", size=12),
        title=dict(text=""),
        legend=dict(font=dict(color=dark)),
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=grid, zeroline=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=grid, zeroline=False)

    return fig


def eco_gauge(score: float) -> go.Figure:
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
            number={"font": {"size": 44, "color": "#0f172a", "family": "Segoe UI, sans-serif"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 0},
                "bar": {"color": bar_color, "thickness": 0.3},
                "bgcolor": "#ffffff",
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
                "font": {"size": 16, "color": "#0f172a"},
            },
        )
    )
    fig.update_layout(hovermode=False, height=320, margin=dict(l=10, r=10, t=50, b=0))
    return apply_plotly_theme(fig)


def time_series(df: pd.DataFrame, x_col: str, y_col: str, label: str, *, height: int = 280, width: float = 2.0) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[x_col], y=df[y_col], mode="lines", name=label, line=dict(width=width)))
    fig.update_traces(hovertemplate="%{y}<extra></extra>")
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=30), xaxis_title=None, yaxis_title=label, height=height)
    return apply_plotly_theme(fig)

def add_band_annotation(
    fig: go.Figure,
    x_start,
    x_end,
    text: str,
    *,
    y: float = 0.95,
    color: str = "rgba(239,68,68,0.12)",
) -> None:
    """
    Adds a shaded vertical band + annotation text.
    Used to highlight inefficient driving zones.
    """
    fig.add_vrect(
        x0=x_start,
        x1=x_end,
        fillcolor=color,
        opacity=0.6,
        line_width=0,
        layer="below",
    )

    fig.add_annotation(
        x=x_start,
        y=y,
        xref="x",
        yref="paper",
        text=text,
        showarrow=False,
        align="left",
        font=dict(size=11, color="#0f172a"),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="rgba(15,23,42,0.15)",
        borderwidth=1,
        borderpad=6,
    )

# =========================
# NAV
# =========================

def set_page(page_name: str) -> None:
    st.session_state.page = page_name


def sidebar_nav_button(label: str, icon: str, page_name: str) -> None:
    slug = slugify(page_name)
    st.button(
        f"{icon}  {label}",
        key=f"nav_{slug}",
        use_container_width=True,
        on_click=set_page,
        args=(page_name,),
    )


# =========================
# SMALL HELPERS
# =========================

def find_first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for cand in candidates:
        if cand in df.columns:
            return cand
    return None


def get_selected_trip_row(
    filtered_trip_stats: pd.DataFrame,
    selected_trip_id,
    trip_id_col: str | None,
) -> pd.Series | None:
    if filtered_trip_stats.empty:
        return None

    if selected_trip_id is None:
        return filtered_trip_stats.iloc[0]

    if trip_id_col:
        matches = filtered_trip_stats[filtered_trip_stats[trip_id_col] == selected_trip_id]
        return matches.iloc[0] if not matches.empty else None

    return filtered_trip_stats.loc[selected_trip_id]


def build_x_axis(trip_obd_df: pd.DataFrame, selected_trip_id) -> tuple[pd.DataFrame, str]:
    """
    Returns: (possibly updated df, x_col)
    Tries TripDateTime based on `YYYY-MM-DD_...` prefix in trip filename + Timestamp.
    Falls back to Timestamp/time/datetime, else index.
    """
    trip_date_str = selected_trip_id.split("_")[0] if isinstance(selected_trip_id, str) else None

    if trip_date_str and "Timestamp" in trip_obd_df.columns:
        base_date = pd.to_datetime(trip_date_str, errors="coerce")

        if pd.api.types.is_numeric_dtype(trip_obd_df["Timestamp"]):
            trip_obd_df["TripDateTime"] = base_date + pd.to_timedelta(trip_obd_df["Timestamp"], unit="s")
        else:
            trip_obd_df["TripDateTime"] = pd.to_datetime(
                trip_obd_df["Timestamp"].astype(str).apply(lambda t: f"{trip_date_str} {t}"),
                errors="coerce",
            )
        return trip_obd_df, "TripDateTime"

    for cand in ["Timestamp", "timestamp", "time", "datetime"]:
        if cand in trip_obd_df.columns:
            return trip_obd_df, cand

    if "index" not in trip_obd_df.columns:
        trip_obd_df = trip_obd_df.reset_index().rename(columns={"index": "index"})
    return trip_obd_df, "index"


def render_insight(ins: dict) -> None:
    sev = ins["severity"]
    styles = {
        "bad": ("#ef4444", "rgba(239,68,68,0.08)"),
        "warn": ("#f59e0b", "rgba(245,158,11,0.08)"),
        "good": ("#10b981", "rgba(16,185,129,0.08)"),
    }
    border, bg = styles.get(sev, ("#9ca3af", "rgba(148,163,184,0.08)"))

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
          <div style="font-weight:600; margin-bottom:2px;">{ins['title']}</div>
          <div style="color:#0f172a;">{ins['text']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def eco_story_card(row: pd.Series, eco_score: float) -> str:
    """
    Returns the HTML for the trip summary card.
    Safe against missing columns.
    """
    status = classify_eco_status(eco_score).lower()

    fuel = row.get("Avg_Fuel_L/100km")
    idle = row.get("Long_Idle_Time_%")
    accel = row.get("Accel_Events")

    fuel_txt = f"{float(fuel):.2f} L/100km" if pd.notna(fuel) else "N/A"
    idle_txt = f"{float(idle):.0f}%" if pd.notna(idle) else "N/A"
    accel_txt = f"{int(accel)}" if pd.notna(accel) else "N/A"

    return f"""
    <div style="
        background:#ffffff;
        border-left:4px solid #9ca3af;
        padding:14px;
        border-radius:10px;
        margin-bottom:14px;
        font-size:14px;
    ">
      <b>This trip was {status}</b>:
      fuel usage was <b>{fuel_txt}</b>,
      with <b>{idle_txt}</b> idle time and
      <b>{accel_txt}</b> acceleration events.
    </div>
    """

# =========================
# MAIN APP
# =========================

def main() -> None:
    st.markdown('<a name="eco-score"></a>', unsafe_allow_html=True)

    # ---------- HEADER ----------
    st.markdown(
        """
        <div style="display:flex; flex-direction:column; gap:4px; margin-bottom:18px;">
          <div style="font-size:26px; font-weight:700; color:#0f172a;">EcoGranite</div>
          <div style="font-size:13px; color:#9ca3af;">Fuel efficiency coach for OBD-II trips</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.subheader("Main menu")

        if "page" not in st.session_state:
            st.session_state.page = "Dashboard"

        inject_css(st.session_state.page)

        sidebar_nav_button("Dashboard", "⏲", "Dashboard")
        sidebar_nav_button("Granite feedback", "✉", "Granite feedback")

        selected_page = st.session_state.page

        if selected_page == "Dashboard":
            st.caption("Dashboard sections")
            st.markdown(
                """
                <div style="display:flex; flex-direction:column; gap:6px; margin-left:8px;">
                  <a href="#eco-score">• Eco score</a>
                  <a href="#insights">• Driving insights</a>
                  <a href="#speed">• Speed profile</a>
                  <a href="#rpm">• RPM profile</a>
                  <a href="#fuel">• Fuel consumption</a>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()
        st.header("Trip data")

        uploaded_file = st.file_uploader(
            "Upload OBD-II CSV",
            type=["csv"],
            help="KIT OBD-II data or your own.",
            key="obd_uploader",
        )
        
        with st.expander("Expected CSV format"):
            st.markdown("""
            Uploaded datasets should contain the core OBD-II telemetry signals used by the EcoGranite analytics pipeline.

            **Required raw columns (KIT OBD-II format):**
            - `engine_rpm_[rpm]`
            - `vehicle_speed_sensor_[km/h]`
            - `air_flow_rate_from_mass_flow_sensor_[g/s]`
            - `time` or `gps_time`

            Additional columns are allowed but not required.
            """)

        use_demo = st.checkbox("Use demo dataset", value=True if not uploaded_file else False)

        using_uploaded_data = uploaded_file is not None and not use_demo

        if using_uploaded_data:
            try:
                obd_df = pd.read_csv(uploaded_file)
                obd_df = normalize_uploaded_obd_columns(obd_df)
            except Exception:
                st.error("Could not read uploaded file as CSV.")
                obd_df = pd.DataFrame()
        elif use_demo:
            obd_df = load_demo_obd()
        else:
            obd_df = pd.DataFrame()

        st.caption("OBD-II columns:")
        st.code(", ".join(obd_df.columns), language="text")

        if using_uploaded_data:
            trip_stats_df = build_trip_stats_from_obd(obd_df)
        else:
            trip_stats_df = load_trip_stats()

            if not trip_stats_df.empty:
                trip_stats_df = trip_stats_df.copy()
                trip_stats_df["Eco_Score"] = trip_stats_df.apply(
                    compute_overall_eco_score, axis=1
                )

        trip_id_col = find_first_col(trip_stats_df, ["Trip", "trip_id", "Trip_ID", "tripId", "trip"])

        filter_mode = st.radio(
            "Highlight trips by",
            [
                "All trips",
                "Efficient trips (Eco ≥ 70)",
                "Moderate trips (40 ≤ Eco < 70)",
                "Not efficient trips (Eco < 40)",
                "High idle",
                "High RPM",
                "High fuel use",
            ],
            index=0,
        )

        filtered_trip_stats = trip_stats_df.copy()
        filter_caption = ""

        if not trip_stats_df.empty and trip_id_col:
        
            if filter_mode == "Efficient trips (Eco ≥ 70)" and "Eco_Score" in trip_stats_df.columns:
                filtered_trip_stats = trip_stats_df[
                    trip_stats_df["Eco_Score"] >= 70
                ]
                filter_caption = "Trips classified as Efficient (Eco Score ≥ 70)."

            elif filter_mode == "Moderate trips (40 ≤ Eco < 70)" and "Eco_Score" in trip_stats_df.columns:
                filtered_trip_stats = trip_stats_df[
                    (trip_stats_df["Eco_Score"] >= 40) & (trip_stats_df["Eco_Score"] < 70)
                ]
                filter_caption = "Trips classified as Moderate (40 ≤ Eco Score < 70)."

            elif filter_mode == "Not efficient trips (Eco < 40)" and "Eco_Score" in trip_stats_df.columns:
                filtered_trip_stats = trip_stats_df[
                    trip_stats_df["Eco_Score"] < 40
                ]
                filter_caption = "Trips classified as In need of improvement (Eco Score < 40)."

            if filter_mode == "High idle" and "Long_Idle_Time_%" in trip_stats_df.columns:
                filtered_trip_stats = trip_stats_df[trip_stats_df["Long_Idle_Time_%"].fillna(0.0) >= 50.0]
                filter_caption = "Trips with idle time ≥ 50% (very high idle)."

            elif filter_mode == "High RPM" and "HighRPM_LowSpeed_%" in trip_stats_df.columns:
                filtered_trip_stats = trip_stats_df[trip_stats_df["HighRPM_LowSpeed_%"].fillna(0.0) >= 0.5]
                filter_caption = "Trips with ≥ 0.5% time at high RPM and low speed."

            elif filter_mode == "High fuel use" and "Avg_Fuel_L/100km" in trip_stats_df.columns:
                filtered_trip_stats = trip_stats_df[trip_stats_df["Avg_Fuel_L/100km"].fillna(0.0) >= 0.40]
                filter_caption = "Trips with avg fuel ≥ 0.40 L/100km (high usage)."

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
            selected_trip_id = None
            st.caption("No trips available for this filter.")

    # ---------- GUARD ----------
    if obd_df.empty:
        st.info("Upload a CSV or enable the demo dataset in the sidebar to see the dashboard.")
        return

    # ---------- PER-TRIP CONTEXT ----------
    current_trip_row = get_selected_trip_row(filtered_trip_stats, selected_trip_id, trip_id_col)

    # ---------- PER-TRIP OBD DATA ----------
    trip_obd_df = normalize_uploaded_obd_columns(obd_df.copy())

    if selected_trip_id is not None:
        trip_source_col = find_first_col(trip_obd_df, ["source_file", "Trip", "trip_id", "trip"])
        if trip_source_col:
            trip_obd_df = trip_obd_df[trip_obd_df[trip_source_col] == selected_trip_id].copy()

    trip_obd_df, x_col = build_x_axis(trip_obd_df, selected_trip_id)

    speed_col = find_first_col(trip_obd_df, ["Speed_kmh", "speed_kmh", "Speed", "speed", "SPEED", "vehicle_speed", "vss"])
    fuel_col = find_first_col(
        trip_obd_df,
        ["fuel_L_s", "L_per_100km", "fuel_rate", "FuelRate", "FUEL_RATE", "fuel_rate_l_h", "fuel_consumption"],
    )
    rpm_col = find_first_col(trip_obd_df, ["RPM", "engine_rpm", "EngineRPM"])

    # ---------- PAGES ----------
    if selected_page == "Dashboard":
        
        if current_trip_row is None:
            st.info("Select a trip to see the eco score.")
            return

        top_left, top_right = st.columns([1.2, 1])

        with top_left:
            st.subheader("Trip snapshot")

            if current_trip_row is None:
                st.caption("No trip stats available yet.")
            else:
                metric_defs = [
                    ("Avg speed", "Avg_Speed_kmh", "km/h", 1, "Average vehicle speed over the trip."),
                    ("Avg RPM", "Avg_RPM", "", 0, "RPM = engine revolutions per minute (how fast the engine is spinning)."),
                    ("Fuel (avg)", "Avg_Fuel_L/100km", "L/100km", 2, "Average fuel consumption per 100 km (lower is better)."),
                    ("High RPM @ low speed (%)", "HighRPM_LowSpeed_%", "%", 2,
 "Percent of trip time with high engine RPM while vehicle speed is low (inefficient zone)."),
                    ("Long idle time", "Long_Idle_Time_%", "%", 1, "Percentage of total trip time spent idling in continuous stops longer than 30 seconds"),
                    ("Accel events", "Accel_Events", "", 0, "Count of strong acceleration events (hard throttle)."),
                    ("Brake events", "Brake_Events", "", 0, "Count of strong braking events (hard braking)."),
                ]

                cols = st.columns(3)
                for i, (label, col_name, unit, decimals, tooltip) in enumerate(metric_defs):
                    if col_name in current_trip_row.index and pd.notna(current_trip_row[col_name]):
                        val = float(current_trip_row[col_name])
                        display = f"{val:.{decimals}f} {unit}".strip()
                        with cols[i % 3]:
                            st.metric(label=label, value=display, help=tooltip)


        with top_right:
            st.subheader("Trip eco score")

            eco_score = compute_overall_eco_score(current_trip_row)
                
            st.markdown(
                eco_story_card(current_trip_row, eco_score),
                unsafe_allow_html=True,
            )

            st.plotly_chart(eco_gauge(eco_score), use_container_width=True)

            if current_trip_row is not None:
                penalties = compute_penalties(current_trip_row)
                driver_lines = top_drivers_text(penalties, k=2)
                render_story_drivers_card(driver_lines)

        st.markdown('<a name="insights"></a>', unsafe_allow_html=True)
        st.markdown("---")

        st.subheader("Driving insights")

        if current_trip_row is None:
            st.caption("Select a trip to see key positives and pain points.")
        else:
            insights = build_trip_insights(current_trip_row)

            if not insights:
                st.caption("No insights available for this trip.")
            else:
                # ✅ WHAT WENT WELL
                st.markdown("##### What went well")
                good_found = False
                for ins in insights:
                    if ins["severity"] == "good":
                        render_insight(ins)
                        good_found = True
                if not good_found:
                    st.caption("No strong positives detected for this trip.")

                st.markdown("---")

                # ⚠️ WHAT COULD IMPROVE
                st.markdown("##### What could improve")


                for ins in insights:
                    if ins["severity"] in ("warn", "bad"):
                        render_insight(ins)


        st.markdown('<a name="speed"></a>', unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Speed profile")
        if speed_col:
            fig_speed = time_series(trip_obd_df, x_col, speed_col, "Speed")

            # Annotate stop-and-go traffic
            low_speed_mask = trip_obd_df[speed_col] < 10
            if low_speed_mask.any():
                idx = low_speed_mask[low_speed_mask].index
                start = trip_obd_df.loc[idx[0], x_col]
                end = trip_obd_df.loc[idx[-1], x_col]

                add_band_annotation(
                    fig_speed,
                    start,
                    end,
                    "Heavy traffic zone → frequent stops increased fuel use",
                    color="rgba(245,158,11,0.18)",
                )

            st.plotly_chart(fig_speed, use_container_width=True, key="speed_chart")
        else:
            st.caption("Speed column not found in this dataset.")

        st.markdown('<a name="rpm"></a>', unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("RPM profile")
        if rpm_col:
            fig_rpm = time_series(trip_obd_df, x_col, rpm_col, "RPM")

            high_rpm_mask = trip_obd_df[rpm_col] > 3000
            if high_rpm_mask.any():
                idx = high_rpm_mask[high_rpm_mask].index
                start = trip_obd_df.loc[idx[0], x_col]
                end = trip_obd_df.loc[idx[-1], x_col]

                add_band_annotation(
                    fig_rpm,
                    start,
                    end,
                    "High RPM → inefficient gear usage",
                    color="rgba(239,68,68,0.18)",
                )

            st.plotly_chart(fig_rpm, use_container_width=True, key="rpm_chart")
        else:
            st.caption("RPM column not found in this dataset.")

        st.markdown('<a name="fuel"></a>', unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Fuel consumption")
        if fuel_col:
            fig_fuel = time_series(trip_obd_df, x_col, fuel_col, "Fuel rate")

            fuel_spike = trip_obd_df[fuel_col] > trip_obd_df[fuel_col].quantile(0.9)
            if fuel_spike.any():
                idx = fuel_spike[fuel_spike].index
                start = trip_obd_df.loc[idx[0], x_col]
                end = trip_obd_df.loc[idx[-1], x_col]

                add_band_annotation(
                    fig_fuel,
                    start,
                    end,
                    "Fuel spike → hard acceleration or high RPM",
                    color="rgba(239,68,68,0.20)",
                )

            st.plotly_chart(fig_fuel, use_container_width=True, key="fuel_chart")
        else:
            st.caption("Fuel rate column not found in this dataset.")

    elif selected_page == "Granite feedback":
        st.subheader("IBM Granite coaching")

        if current_trip_row is None or selected_trip_id is None:
            st.info("Select a trip first to see Granite coaching.")
            return

        granite_df = load_granite_feedback()
        trip_feedback_df = granite_df.copy()

        if not trip_feedback_df.empty:
            granite_trip_id_col = find_first_col(
                trip_feedback_df,
                ["Trip", "trip_id", "Trip_ID", "tripId", "trip"]
            )

            if selected_trip_id is not None and granite_trip_id_col:
                trip_feedback_df = trip_feedback_df[
                    trip_feedback_df[granite_trip_id_col] == selected_trip_id
                ]

        # 1) Use precomputed feedback if it exists
        if not trip_feedback_df.empty:
            row = trip_feedback_df.iloc[0]
            prompt_text = row.get("prompt", "(no prompt available)")
            feedback_text = row.get("feedback", "(no feedback available)")
            temperature = row.get("temperature", 0.2)
            feedback_source = "precomputed"

        # 2) Otherwise generate live feedback for uploaded/custom trips
        else:
            try:
                prompt_text = build_live_granite_prompt(current_trip_row)

                with st.spinner("Generating live Granite coaching..."):
                    live_result = generate_live_granite_feedback(
                        trip_id=str(selected_trip_id),
                        prompt_text=prompt_text,
                        temperature=0.2,
                    )

                feedback_text = live_result["feedback"]
                temperature = live_result["temperature"]
                feedback_source = "live"

            except Exception as e:
                st.error(f"Could not generate Granite feedback for this trip: {e}")
                st.caption(
                    "Make sure WATSONX_API_KEY is set in your environment and your IBM project/model access is valid."
                )
                return

        st.markdown("**Granite coaching (AI response)**")

        formatted_feedback = str(feedback_text)

        formatted_feedback = formatted_feedback.replace(
            "Overview:",
            "<br><b>Overview</b><br>"
        )

        formatted_feedback = formatted_feedback.replace(
            "Coaching Suggestions:",
            "<br><b>Coaching Suggestions</b><br>"
        )

        formatted_feedback = formatted_feedback.replace(
            "Key Takeaway:",
            "<br><b>Key Takeaway</b><br>"
        )

        st.markdown(
            f"""
            <div style="
                background: rgba(34,197,94,0.07);
                border-left: 3px solid #10b981;
                padding: 14px;
                border-radius: 6px;
                font-size: 13px;
                line-height: 1.7;
                white-space: normal;
            ">{formatted_feedback}</div>
            """,
            unsafe_allow_html=True,
        )

        meta_bits = [f"Model: IBM Granite ({WATSONX_MODEL_ID})", f"Source: {feedback_source}"]
        if temperature is not None:
            meta_bits.append(f"Temperature: {temperature}")

        st.caption(" | ".join(meta_bits))

        with st.expander("Show AI generation details"):
            st.markdown("**Granite prompt (trip summary)**")
            st.code(prompt_text)

if __name__ == "__main__":
    main()
