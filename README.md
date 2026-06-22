# Clearing the Air — NY State PM2.5 Dashboard

An interactive exploratory dashboard analyzing daily fine-particle pollution (PM2.5)
across eight New York State monitoring stations, 2020–2024, following the QUEST
framework for structured exploratory data analysis.

**Deliverable for:** Visual Analytics project (interactive dashboard component).
Built with Streamlit + Plotly. No code appears in any audience-facing view.

---

## What's inside

```
aqi_dashboard/
├── app.py                      # the dashboard
├── requirements.txt            # dependencies
├── .streamlit/config.toml      # theme
└── data/
    └── epa_air_quality.csv     # the dataset (2020–2024)
```

Five views: **Overview** (trend + city/country gap), **Explore** (place comparison,
station map, seasonal pattern, weather scatter, record table), **The 2023 smoke event**,
**Data & sustainability** (full provenance), and **About the method** (QUEST).

Interactive controls (sidebar): date-range slider, community-type filter, station filter,
and a data-replacement uploader. Every chart and KPI recomputes live.

---

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL it prints (usually http://localhost:8501).

---

## Deploy it publicly (Streamlit Community Cloud — free)

1. Push this folder to a **public GitHub repo** (keep the structure above).
2. Go to **https://share.streamlit.io** and sign in with GitHub.
3. Click **New app** → pick the repo/branch → set **Main file path** to `app.py`.
4. Click **Deploy**. First build takes a few minutes.
5. **Verify it loads**, then copy the public `https://<your-app>.streamlit.app` URL into
   your written summary and use it in the video.

> Tip: the assignment allows "Streamlit or an equivalent tool." Tableau Public counts too —
> but this Streamlit version is ready to deploy as-is on the EPA dataset.

---

## Keep the data current (data sustainability)

The dashboard is built to be refreshed, not frozen:

- **Source:** U.S. EPA Outdoor Air Quality Data — https://www.epa.gov/outdoor-air-quality-data
- **Refresh, easy way:** open the deployed app → sidebar → **Replace data** → upload a newer
  CSV that has the same columns. The whole dashboard updates instantly.
- **Refresh, permanent way:** replace `data/epa_air_quality.csv` with the new export
  (same column names) and push to GitHub — the app redeploys automatically.

**Required columns:** `date, station, station_type, latitude, longitude,
pm25_daily_mean, temperature_f, relative_humidity`.

---

## Data notes

- ~5% of PM2.5 readings are blank (monitor downtime) and excluded from averages.
- A few slightly-negative readings (instrument noise) are floored at zero for category labels.
- A handful of daily values near 900+ µg/m³ are implausibly high for a daily mean and are
  flagged as suspect outliers rather than dropped silently.
