"""
Clearing the Air — New York State PM2.5, 2020–2024
An interactive exploratory dashboard built on EPA-style daily monitoring data.

Audience: civic / public-health readers, not engineers. No code is shown in the UI.
Run locally:  streamlit run app.py
"""

import os
from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Page + theme
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Clearing the Air — NY State PM2.5",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# EPA 24-hour PM2.5 AQI category breakpoints (2024 revision), µg/m³
AQI_BANDS = [
    ("Good", 0.0, 9.0, "#46A35E"),
    ("Moderate", 9.1, 35.4, "#E9C46A"),
    ("Unhealthy for sensitive groups", 35.5, 55.4, "#F4A261"),
    ("Unhealthy", 55.5, 125.4, "#E63946"),
    ("Very unhealthy", 125.5, 225.4, "#8E44AD"),
    ("Hazardous", 225.5, 10000, "#7D1128"),
]
CAT_ORDER = [b[0] for b in AQI_BANDS]
CAT_COLOR = {b[0]: b[3] for b in AQI_BANDS}
TYPE_ORDER = ["urban", "suburban", "rural"]
TYPE_COLOR = {"urban": "#E63946", "suburban": "#F4A261", "rural": "#46A35E"}
UNHEALTHY = 35.5  # µg/m³ — sensitive-group threshold and above

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing:-0.01em; color:#1A2421;}
.block-container { padding-top: 1.4rem; max-width: 1250px;}
.kpi { background:#F4F7F6; border:1px solid #E3EAE8; border-radius:14px; padding:16px 18px; height:100%;}
.kpi .label { font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em; color:#5C6B66; font-weight:600;}
.kpi .value { font-family:'IBM Plex Mono', monospace; font-size:1.9rem; font-weight:600; color:#1A2421; line-height:1.1; margin-top:4px;}
.kpi .sub { font-size:0.78rem; color:#5C6B66; margin-top:2px;}
.ribbon { display:flex; border-radius:8px; overflow:hidden; margin:2px 0 10px 0; border:1px solid #E3EAE8;}
.ribbon div { flex:1; padding:5px 6px; font-size:0.66rem; color:#1A2421; text-align:center; font-weight:600;}
.tag { display:inline-block; background:#E7F1EF; color:#1f6f68; border-radius:999px; padding:2px 10px; font-size:0.72rem; font-weight:600; margin-right:6px;}
a { color:#1f6f68;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "epa_air_quality.csv")


def categorize(v):
    if pd.isna(v):
        return np.nan
    v = max(v, 0.0)
    for name, lo, hi, _ in AQI_BANDS:
        if v <= hi:
            return name
    return "Hazardous"


@st.cache_data(show_spinner=False)
def load_data(path_or_buffer):
    df = pd.read_csv(path_or_buffer)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")
    df["season"] = df["month"].map(
        {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
         6: "Summer", 7: "Summer", 8: "Summer", 9: "Fall", 10: "Fall", 11: "Fall"}
    )
    # PM2.5 cleaned for categorisation only (negatives are sensor artifacts -> 0)
    df["pm25_clean"] = df["pm25_daily_mean"].clip(lower=0)
    df["aqi_category"] = df["pm25_daily_mean"].apply(categorize)
    df["is_unhealthy"] = df["pm25_daily_mean"] >= UNHEALTHY
    df["station_type"] = pd.Categorical(df["station_type"], categories=TYPE_ORDER, ordered=True)
    return df


with st.sidebar:
    st.markdown("### Data source")
    st.caption("Default: the project file (2020–2024). To refresh, drop in a newer EPA export with the same columns.")
    up = st.file_uploader("Replace data (optional)", type=["csv"], label_visibility="collapsed")

raw = load_data(up if up is not None else DATA_PATH)

# ----------------------------------------------------------------------------
# Sidebar filters (interactivity)
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("---")
    st.markdown("### Filters")
    dmin, dmax = raw["date"].min().date(), raw["date"].max().date()
    dr = st.slider("Date range", min_value=dmin, max_value=dmax, value=(dmin, dmax), format="MMM YYYY")

    types = st.multiselect("Community type", TYPE_ORDER, default=TYPE_ORDER)
    stations_all = sorted(raw["station"].unique())
    stations = st.multiselect("Stations", stations_all, default=stations_all)

    st.markdown("---")
    st.caption(
        "PM2.5 = fine inhalable particles (smoke, soot, exhaust) ≤2.5 microns wide. "
        "It is the pollutant most tied to heart and lung harm, which is why it anchors this dashboard."
    )

mask = (
    (raw["date"].dt.date >= dr[0]) & (raw["date"].dt.date <= dr[1])
    & (raw["station_type"].astype(str).isin(types))
    & (raw["station"].isin(stations))
)
df = raw[mask].copy()

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown("# Clearing the Air")
st.markdown(
    "#### Who breathes the worst air in New York — and what 2023 changed"
)
st.markdown(
    "<span class='tag'>QUEST exploratory analysis</span>"
    "<span class='tag'>8 monitoring stations</span>"
    "<span class='tag'>2020–2024 · daily PM2.5</span>",
    unsafe_allow_html=True,
)
st.write(
    "Most days, New York's air is clean. But the daily average hides two stories: a steady gap "
    "between city and country air, and rare smoke episodes that briefly make the air hazardous for everyone. "
    "Use the filters on the left to explore by place, community type, and time. Every view answers one question — "
    "and the answers tend to raise the next one."
)

# AQI legend ribbon
ribbon = "".join(
    f"<div style='background:{c}1A;border-bottom:3px solid {c}'>{n}</div>"
    for n, _, _, c in AQI_BANDS
)
st.markdown(f"<div class='ribbon'>{ribbon}</div>", unsafe_allow_html=True)
st.caption("EPA 24-hour PM2.5 air-quality categories (2024 breakpoints), in micrograms per cubic meter of air.")

if df.empty:
    st.warning("No data matches the current filters. Widen the date range or add stations.")
    st.stop()

# ----------------------------------------------------------------------------
# KPI row
# ----------------------------------------------------------------------------
valid = df["pm25_daily_mean"].dropna()
avg_pm = valid.mean()
good_share = (df["aqi_category"] == "Good").mean() * 100
unhealthy_days = int(df["is_unhealthy"].sum())
worst = (
    df.groupby("station")["pm25_daily_mean"].mean().sort_values(ascending=False)
    if df["station"].nunique() else pd.Series(dtype=float)
)
worst_station = worst.index[0] if len(worst) else "—"
worst_val = worst.iloc[0] if len(worst) else np.nan


def kpi(col, label, value, sub):
    col.markdown(
        f"<div class='kpi'><div class='label'>{label}</div>"
        f"<div class='value'>{value}</div><div class='sub'>{sub}</div></div>",
        unsafe_allow_html=True,
    )


c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Average PM2.5", f"{avg_pm:.1f}", "µg/m³ over current selection")
kpi(c2, "Clean-air days", f"{good_share:.0f}%", "rated “Good” (≤9 µg/m³)")
kpi(c3, "Unhealthy days", f"{unhealthy_days:,}", "≥35.5 µg/m³ (sensitive groups +)")
kpi(c4, "Worst location", worst_station, f"{worst_val:.1f} µg/m³ average")
st.write("")

# ----------------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------------
tab_over, tab_explore, tab_event, tab_data, tab_about = st.tabs(
    ["Overview", "Explore", "The 2023 smoke event", "Data & sustainability", "About the method"]
)

# ===== OVERVIEW =====
with tab_over:
    st.markdown("### The trend at a glance")
    st.write(
        "Monthly average PM2.5 across the selected stations. Watch 2023: a sharp, statewide spike that "
        "stands out against four otherwise stable years."
    )
    monthly = (
        df.dropna(subset=["pm25_daily_mean"])
        .groupby([pd.Grouper(key="date", freq="MS"), "station_type"], observed=True)["pm25_daily_mean"]
        .mean().reset_index()
    )
    fig = px.line(
        monthly, x="date", y="pm25_daily_mean", color="station_type",
        color_discrete_map=TYPE_COLOR, category_orders={"station_type": TYPE_ORDER},
        labels={"pm25_daily_mean": "PM2.5 (µg/m³)", "date": "", "station_type": "Community type"},
    )
    fig.add_hline(y=UNHEALTHY, line_dash="dot", line_color="#E63946",
                  annotation_text="Unhealthy threshold (35.5)", annotation_position="top left")
    fig.update_layout(height=380, legend_title_text="", margin=dict(t=10, b=0, l=0, r=0),
                      plot_bgcolor="white", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    colA, colB = st.columns([3, 2])
    with colA:
        st.markdown("### The city–country gap")
        st.write(
            "Average PM2.5 by community type. Urban stations carry a consistently heavier particle load than "
            "rural ones — an exposure gap that holds across all five years."
        )
        bytype = df.dropna(subset=["pm25_daily_mean"]).groupby("station_type", observed=True)["pm25_daily_mean"].mean().reset_index()
        figb = px.bar(bytype, x="station_type", y="pm25_daily_mean", color="station_type",
                      color_discrete_map=TYPE_COLOR, category_orders={"station_type": TYPE_ORDER},
                      labels={"pm25_daily_mean": "Avg PM2.5 (µg/m³)", "station_type": ""})
        figb.update_layout(height=330, showlegend=False, margin=dict(t=10, b=0, l=0, r=0), plot_bgcolor="white")
        st.plotly_chart(figb, use_container_width=True)
    with colB:
        st.markdown("### What the air was rated")
        st.write("Share of days in each EPA air-quality category for the current selection.")
        catshare = df["aqi_category"].value_counts(normalize=True).reindex(CAT_ORDER).dropna().reset_index()
        catshare.columns = ["aqi_category", "share"]
        figd = px.bar(catshare, x="share", y="aqi_category", orientation="h", color="aqi_category",
                      color_discrete_map=CAT_COLOR, category_orders={"aqi_category": CAT_ORDER[::-1]},
                      labels={"share": "Share of days", "aqi_category": ""})
        figd.update_layout(height=330, showlegend=False, margin=dict(t=10, b=0, l=0, r=0),
                           plot_bgcolor="white", xaxis_tickformat=".0%")
        st.plotly_chart(figd, use_container_width=True)

    st.info(
        "**Reading the room:** clean air is the norm (most days are Good or Moderate), but the average is "
        "dragged up by a small number of severe days — and those land disproportionately on urban communities."
    )

# ===== EXPLORE =====
with tab_explore:
    st.markdown("### Compare places")
    st.write("Average PM2.5 by station, colored by community type. Reorder the story by filtering on the left.")
    bystation = (
        df.dropna(subset=["pm25_daily_mean"]).groupby(["station", "station_type"], observed=True)["pm25_daily_mean"]
        .mean().reset_index().sort_values("pm25_daily_mean")
    )
    figs = px.bar(bystation, x="pm25_daily_mean", y="station", orientation="h", color="station_type",
                  color_discrete_map=TYPE_COLOR, category_orders={"station_type": TYPE_ORDER},
                  labels={"pm25_daily_mean": "Avg PM2.5 (µg/m³)", "station": "", "station_type": "Type"})
    figs.update_layout(height=360, margin=dict(t=10, b=0, l=0, r=0), plot_bgcolor="white", legend_title_text="")
    st.plotly_chart(figs, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Where the stations are")
        st.write("Each point is a monitor, sized and colored by its average PM2.5. Smog rises toward the cities.")
        geo = (
            df.dropna(subset=["pm25_daily_mean"]).groupby(["station", "latitude", "longitude"], observed=True)
            .agg(pm25=("pm25_daily_mean", "mean")).reset_index()
        )
        figm = px.scatter_mapbox(
            geo, lat="latitude", lon="longitude", size="pm25", color="pm25",
            color_continuous_scale=["#46A35E", "#E9C46A", "#F4A261", "#E63946"],
            size_max=26, zoom=5.4, hover_name="station",
            hover_data={"pm25": ":.1f", "latitude": False, "longitude": False},
        )
        figm.update_layout(mapbox_style="open-street-map", height=360,
                           margin=dict(t=0, b=0, l=0, r=0), coloraxis_colorbar_title="PM2.5")
        st.plotly_chart(figm, use_container_width=True)
    with col2:
        st.markdown("### The shape of the year")
        st.write("Average PM2.5 by month. Particle pollution has a seasonal rhythm, peaking in the warm-weather smoke season.")
        bymonth = (
            df.dropna(subset=["pm25_daily_mean"]).groupby("month", observed=True)["pm25_daily_mean"].mean().reset_index()
        )
        bymonth["month_name"] = bymonth["month"].apply(lambda m: date(2020, m, 1).strftime("%b"))
        figmo = px.area(bymonth, x="month_name", y="pm25_daily_mean", markers=True,
                        labels={"pm25_daily_mean": "Avg PM2.5 (µg/m³)", "month_name": ""})
        figmo.update_traces(line_color="#2A9D8F", fillcolor="rgba(42,157,143,0.15)")
        figmo.update_layout(height=360, margin=dict(t=10, b=0, l=0, r=0), plot_bgcolor="white")
        st.plotly_chart(figmo, use_container_width=True)

    st.markdown("### Does weather move the needle?")
    st.write(
        "Each dot is one station-day: temperature against PM2.5. A mild warm-weather association appears, "
        "but the worst spikes are episodic — driven by smoke, not heat alone."
    )
    samp = df.dropna(subset=["pm25_daily_mean", "temperature_f"])
    if len(samp) > 6000:
        samp = samp.sample(6000, random_state=7)
    figsc = px.scatter(samp, x="temperature_f", y="pm25_daily_mean", color="station_type",
                       color_discrete_map=TYPE_COLOR, category_orders={"station_type": TYPE_ORDER},
                       opacity=0.45, labels={"temperature_f": "Temperature (°F)", "pm25_daily_mean": "PM2.5 (µg/m³)",
                                             "station_type": "Type"})
    figsc.update_layout(height=340, margin=dict(t=10, b=0, l=0, r=0), plot_bgcolor="white", legend_title_text="")
    figsc.update_yaxes(range=[0, min(200, samp["pm25_daily_mean"].quantile(0.999))])
    st.plotly_chart(figsc, use_container_width=True)

    st.markdown("### Inspect the records")
    st.write("Filtered daily readings. Sort any column; download what you see.")
    show = (
        df[["date", "station", "station_type", "pm25_daily_mean", "aqi_category", "temperature_f", "relative_humidity"]]
        .sort_values("pm25_daily_mean", ascending=False)
        .rename(columns={"pm25_daily_mean": "PM2.5", "station_type": "type", "temperature_f": "temp °F",
                         "relative_humidity": "humidity %", "aqi_category": "AQI category"})
    )
    st.dataframe(show, use_container_width=True, height=300, hide_index=True)
    st.download_button("Download filtered data (CSV)", show.to_csv(index=False).encode(),
                       "ny_pm25_filtered.csv", "text/csv")

# ===== 2023 EVENT =====
with tab_event:
    st.markdown("### The year the smoke arrived")
    st.write(
        "In June 2023, smoke from Canadian wildfires drifted across the Northeast and turned skies orange. "
        "In this data, 2023 stands apart: the count of unhealthy-air days jumped roughly tenfold before "
        "snapping back in 2024. A clean five-year average would have hidden it completely — which is exactly why "
        "exploration beats summary statistics."
    )
    yearly = raw.groupby("year").agg(
        unhealthy=("is_unhealthy", "sum"), avg=("pm25_daily_mean", "mean")
    ).reset_index()
    col1, col2 = st.columns(2)
    with col1:
        figy = px.bar(yearly, x="year", y="unhealthy", labels={"unhealthy": "Unhealthy-air days", "year": ""},
                      text="unhealthy")
        figy.update_traces(marker_color="#E63946", textposition="outside")
        figy.update_layout(height=340, margin=dict(t=10, b=0, l=0, r=0), plot_bgcolor="white")
        st.plotly_chart(figy, use_container_width=True)
        st.caption("Statewide count of days at or above 35.5 µg/m³ (all stations), by year.")
    with col2:
        figavg = px.line(yearly, x="year", y="avg", markers=True,
                         labels={"avg": "Avg PM2.5 (µg/m³)", "year": ""})
        figavg.update_traces(line_color="#2A9D8F")
        figavg.update_layout(height=340, margin=dict(t=10, b=0, l=0, r=0), plot_bgcolor="white")
        st.plotly_chart(figavg, use_container_width=True)
        st.caption("Statewide average PM2.5 by year. The 2023 bump is modest in the average but severe in the tails.")

    st.markdown("### The worst single days on record")
    top = (
        raw.dropna(subset=["pm25_daily_mean"]).nlargest(12, "pm25_daily_mean")
        [["date", "station", "station_type", "pm25_daily_mean", "aqi_category"]]
        .rename(columns={"pm25_daily_mean": "PM2.5", "station_type": "type", "aqi_category": "AQI category"})
    )
    top["date"] = top["date"].dt.strftime("%b %d, %Y")
    st.dataframe(top, use_container_width=True, hide_index=True)
    st.caption(
        "Note the extreme top values: a few readings near 900+ µg/m³ are far above any plausible daily mean and "
        "are treated in this project as sensor artifacts/outliers — a reminder to interrogate, not trust, the maximum."
    )

# ===== DATA & SUSTAINABILITY =====
with tab_data:
    st.markdown("### Data source & how to keep this current")
    st.write(
        "This dashboard follows the principle of *data sustainability*: it is built to be refreshed, not frozen. "
        "Everything below documents where the data comes from and how a future reader can update it."
    )
    meta = pd.DataFrame({
        "Item": ["Source", "Dataset", "Coverage", "Stations", "Rows × columns",
                 "Date accessed", "License / terms", "Refresh method"],
        "Detail": [
            "U.S. EPA outdoor air quality monitoring data (Air Quality System / AirData)",
            "Daily PM2.5 with co-located temperature and relative humidity, New York State",
            "Jan 1, 2020 – Dec 31, 2024 (daily)",
            "8 stations across urban, suburban, and rural New York",
            f"{raw.shape[0]:,} rows × {raw.shape[1] - 7} source columns",
            "March 2026 (confirm your exact download date)",
            "Public domain — U.S. Government work, free to use with attribution",
            "Re-download the latest daily summary from EPA AirData, keep the same column names, "
            "and upload it with the sidebar uploader (or replace data/epa_air_quality.csv and redeploy).",
        ],
    })
    st.table(meta)
    st.markdown(
        "**Source portal:** [EPA Outdoor Air Quality Data](https://www.epa.gov/outdoor-air-quality-data) · "
        "**Live conditions:** [AirNow.gov](https://www.airnow.gov)"
    )
    st.markdown("### Data-quality notes")
    st.markdown(
        "- **Missing values:** about 5% of PM2.5 readings are blank (monitor downtime); these days are excluded from averages.\n"
        "- **Negative values:** a few readings dip slightly below zero — instrument noise near the detection limit — "
        "and are floored at zero for air-quality category assignment.\n"
        "- **Outliers:** a handful of daily values near 900+ µg/m³ exceed any realistic daily mean and are flagged as "
        "suspect rather than dropped silently.\n"
        "- **Scope:** these are eight fixed monitors, not a wall-to-wall map; neighborhoods without a monitor are not represented."
    )

# ===== ABOUT =====
with tab_about:
    st.markdown("### How this analysis was done — the QUEST framework")
    st.write("EDA as detective work: every view answers a specific question, and every answer opens the next one.")
    quest = pd.DataFrame({
        "Phase": ["Question", "Understand", "Explore", "Synthesize", "Tell"],
        "What happened here": [
            "Framed the guiding questions: How clean is NY air? Is exposure equal across communities? "
            "Is it improving? What caused any anomalies?",
            "Profiled the data — eight stations, five years, daily PM2.5 plus weather — and audited quality "
            "(missingness, negatives, outliers) before trusting a single chart.",
            "Built trend, place-comparison, map, seasonal, and weather views, letting surprises (the 2023 spike) "
            "redirect the questions.",
            "Connected the threads: a persistent urban–rural gap, a seasonal rhythm, and rare acute smoke episodes "
            "that the average alone conceals.",
            "Translated findings into this dashboard and a plain-language briefing with recommendations for a "
            "non-technical audience.",
        ],
    })
    st.table(quest)
    st.markdown(
        "**Guiding principles applied:** exploration over bookkeeping; a willingness to be surprised (the 2023 "
        "anomaly reshaped the story); and automation that accelerates — but does not replace — human judgment about "
        "what the numbers mean."
    )
    st.caption("Built with Streamlit and Plotly. No code is shown in the audience-facing views, by design.")

st.markdown("---")
st.caption(
    "Clearing the Air · Exploratory data analysis of New York State PM2.5, 2020–2024 · "
    "Source: U.S. EPA outdoor air quality monitoring data · Built for a general audience."
)
