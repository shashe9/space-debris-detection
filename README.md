# Space Debris Detection & Satellite Orbit Visualization

> **Repository:** [https://github.com/shashe9/space-debris-detection](https://github.com/shashe9/space-debris-detection)
> **Owner:** Shashank Shekhar
> **Status:** Working prototype — orbit simulation, ingestion of Starlink metadata, risk scoring, position enrichment, interactive Streamlit dashboard, collision-detection tooling. Ready for AI/ML integration.

---

This README summarizes everything done so far, how the pieces fit together, how to run them locally, and the recommended next steps (ML, forecasting, anomaly detection, dashboard UX polish, deployment).

---

# Table of contents

* [Project overview](#project-overview)
* [Status — what’s implemented](#status---whats-implemented)
* [Repository structure (current)](#repository-structure-current)
* [Data files & schemas (what each CSV contains)](#data-files--schemas-what-each-csv-contains)
* [Quickstart (run locally)](#quickstart-run-locally)

  * prerequisites
  * create & activate venv
  * install dependencies
  * run simulation (single sat)
  * generate all-sat orbits from metadata
  * generate collisions & risk files
  * enrich with positions
  * run dashboard
* [How each script is meant to be used (workflow)](#how-each-script-is-meant-to-be-used-workflow)
* [AI / ML roadmap & recommended files](#ai--ml-roadmap--recommended-files)
* [Tips, troubleshooting & gotchas (common errors)](#tips-troubleshooting--gotchas-common-errors)
* [Git / large files guidelines](#git--large-files-guidelines)
* [Next steps & recommended improvements](#next-steps--recommended-improvements)
* [Contributing](#contributing)
* [License & credits](#license--credits)

---

# Project overview

This project simulates satellite orbits (example single-satellite `simulate_orbit.py`), ingests Starlink orbital metadata (CSV exported from Celestrak), generates per-timestamp satellite positions for many satellites, computes pairwise close approaches, scores the encounters (heuristic risk score + persistence), enriches risk events with the satellites’ positions, and presents the results in an interactive Streamlit dashboard (`scripts/dashboard.py`) for visualization and exploration.

The pipeline is intentionally modular:

* Simulation / orbit generation (Skyfield)
* Collision detection & scoring (pandas / numpy)
* Enrichment (merge orbit positions into events)
* Dashboarding (Streamlit + Plotly)
* Planned ML components (classification, anomaly detection, forecasting)

---

# Status — what's implemented

Major implemented items (as of now):

* Orbit simulation for a single TLE (`scripts/simulate_orbit.py`) — produces `data/satellite_orbit_track.csv` and some plots.
* Tools that transform Celestrak-like CSV metadata (Starlink metadata) into simulated per-satellite orbit tracks (`data/all_satellite_orbits.csv`) — this was implemented and used to create the big orbit CSV.
* Collision detection script(s) that:

  * group by timestamp and compute pairwise 3D distance using Haversine for surface distance + altitude delta,
  * compute a `Streak` for consecutive appearances,
  * compute a simple `Risk Score` = `(1 / (distance + 1)) * (1 + streak)`,
  * save `collision_risks.csv` (raw risk events).
* Persistence detection and scoring (`scripts/generate_risk_scores.py`) that:

  * produces `data/persistent_risks.csv` (and optionally `persistent_risks_with_positions.csv`),
  * appends Lat/Lon/Altitude for each satellite pair by merging from `data/all_satellite_orbits.csv`.
* Streamlit dashboard (`scripts/dashboard.py`) with:

  * sidebar filters (date range, distance slider up to 5,000 m, risk levels),
  * tabs & sub-views,
  * bar chart with moving average, pie chart with fixed color mapping, interactive Plotly map with real positions, altitude vs distance scatter, top-satellites bar chart, and a detailed event log.
* Styling/CSS to make the dashboard use more horizontal space and responsive Plotly elements.
* Worked out common errors & fixes (timezone issues, Skyfield API misuses, CSV column naming mismatches, etc.)

---

# Repository structure (current)

```
Space_Debris_Detection_Project/
│
├── data/
│   ├── all_satellite_orbits.csv            # (big) per-satellite, per-timestamp orbit positions
│   ├── satellite_orbit_track.csv           # single-satellite example produced by simulate_orbit.py
│   ├── starlink_metadata.csv               # raw exported metadata from Celestrak (input)
│   ├── collision_risks.csv                 # pairwise collision raw results (Distance, Timestamp, sat1, sat2)
│   ├── persistent_risks.csv                # scored & enriched risk events (with Lat1/Lon1/Lat2/Lon2/Avg)
│   └── persistent_risks_with_positions.csv # optional intermediate; same as above in some flows
│
├── scripts/
│   ├── simulate_orbit.py                   # original one-sat simulation + plotting
│   ├── GenerateAllOrbitsFromMetadata.py    # (or similar) script: reads starlink_metadata.csv and creates all_satellite_orbits.csv
│   ├── detect_collisions.py                 # simple pairwise detection example
│   ├── generate_risk_scores.py             # computes streak and risk_score (and appends pos columns)
│   ├── detect_collisions_with_velocity.py  # (optional) collision detection that also computes relative velocity
│   └── dashboard.py                         # Streamlit app (UI & visuals)
│
│
├── plots/                                   # generated plots (orbit_track.png, 3d_orbit.png, etc.)
│
├── requirements.txt                         # project dependencies
├── .gitignore
└── README.md
```

> NOTE: Some script names may differ slightly.

---

# Data files & schemas (what each CSV contains)

Below are the common CSV shapes you will encounter.

### `data/all_satellite_orbits.csv`

Per-satellite time series produced by orbit simulation (for many satellites).

Columns:

```
Satellite Name, Time (UTC), Latitude, Longitude, Altitude (m)
STARLINK-1008, 2025-07-25T19:09:52Z, 3.218e-05, -106.0387, 548467.9757
...
```

### `data/collision_risks.csv`

Raw detected close approaches (pairwise at same timestamp).

Columns:

```
Timestamp, Satellite 1, Satellite 2, Distance (m)
2025-07-26T16:48:20Z, STARLINK-34185, STARLINK-34592, 445.55
...
```

### `data/persistent_risks.csv` (final used by dashboard)

Scored & enriched events (streak, risk score, position columns merged in):

Columns:

```
Timestamp, Satellite 1, Satellite 2, Distance (m), Streak, Risk Score,
Lat1, Lon1, Alt1, Lat2, Lon2, Alt2, Latitude, Longitude, Avg Altitude
```

`Latitude, Longitude` are usually the average/centroid between the pair — used for mapping.

---

# Quickstart — run locally

Below are concise steps to set up the project locally on Windows (PowerShell) or Linux/macOS.

> **Python version:** 3.9–3.11 recommended.

## 1) Clone repo

```bash
git clone https://github.com/shashe9/space-debris-detection.git
cd space-debris-detection
```

## 2) Create virtual environment

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows CMD**

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/macOS (bash/zsh)**

```bash
python3 -m venv venv
source venv/bin/activate
```

You should now see `(venv)` in your prompt.

## 3) Install dependencies


```bash
pip install -r requirements.txt
```

**Recommended packages**

```bash
pip install pandas numpy matplotlib plotly streamlit scikit-learn joblib shap xgboost skyfield imageio-ffmpeg
```

> *Note:* `skyfield` is required for orbit propagation. `plotly` + `streamlit` for the dashboard. `scikit-learn` / `xgboost` / `joblib` for ML.

## 4) Prepare data inputs

* Put the Celestrak/Starlink metadata CSV into `data/starlink_metadata.csv` (the header row + rows of element fields).
* If you already have `data/all_satellite_orbits.csv` (generated earlier), you can skip regeneration.

## 5) Generate all satellite orbit tracks (if needed)

If you want to create `data/all_satellite_orbits.csv` from metadata:

```bash
python scripts/GenerateAllOrbitsFromMetadata.py
```

(If your script has another name, run that script. This script reads `data/starlink_metadata.csv` and simulates positions for each satellite over the 24-hour window.)

## 6) Run collision detection + scoring

* Generate pairwise collisions:

```bash
python scripts/detect_collisions.py
# produces data/collision_risks.csv
```

* Compute persistence & risk score and enrich with positions:

```bash
python scripts/generate_risk_scores.py
# produces data/persistent_risks.csv (and optionally persistent_risks_with_positions.csv)
```

> Tip: `generate_risk_scores.py` expects `data/collision_risks.csv` to exist.

## 7) Run the Streamlit dashboard

**Recommended** (ensures correct Streamlit runtime):

```bash
python -m streamlit run scripts/dashboard.py
```

Or, if you have `streamlit` in PATH:

```bash
streamlit run scripts/dashboard.py
```

Open the link printed by Streamlit (usually `http://localhost:8501`).

---

# How each script is meant to be used (workflow)

Typical flow:

1. Download Starlink/Celestrak metadata (`data/starlink_metadata.csv`).
2. Run orbit generation script(s) → `data/all_satellite_orbits.csv`.
3. Run pairwise detection → `data/collision_risks.csv`.
4. Run persistence/risk scoring → `data/persistent_risks.csv`.
5. Launch dashboard to analyze and visualize (`scripts/dashboard.py`).
6. (Optional) Train ML model on `persistent_risks.csv` to predict/validate risk levels.

---

# AI / ML roadmap & recommended files

We will integrate ML in phases. Suggested filenames & roles:

* `scripts/train_risk_model.py`

  * Loads `data/persistent_risks.csv`
  * Prepares features (Distance, Streak, Avg Altitude, Hour of day, optionally relative velocity)
  * Trains models (RandomForest/XGBoost baseline)
  * Evaluates and saves model (e.g. `models/risk_classifier.pkl`)

* `scripts/detect_anomalies.py`

  * Runs isolation forest / clustering to flag rare events
  * Writes `data/anomalies.csv`

* Dashboard integration:

  * Update `scripts/dashboard.py` to load `models/risk_classifier.pkl` (via `joblib`) and show an AI-predicted risk label + probability.

**Suggested ML features**:

* `Distance (m)` (direct)
* `Streak` (persistence)
* `Avg Altitude` (m)
* `Hour_of_day`, `Day_of_week` (cyclical/time features)
* `Relative Velocity` (if available)

**Libraries**:

* scikit-learn, xgboost, joblib, shap for explanations, prophet or statsmodels for time-series

---

# Tips, troubleshooting & gotchas

* **Skyfield/Timezone**: When converting epochs or datetimes for Skyfield, make sure datetimes have timezone info (UTC). Example:

```python
from skyfield.api import utc
dt = datetime(2025, 7, 25, 19, 9, 52, tzinfo=utc)
```

Errors like `cannot interpret a datetime that lacks a timezone` mean you need to attach `tzinfo=utc`.

* **EarthSatellite.from\_elements**: older/alternate Skyfield APIs may not expose `from_elements`. If you encounter `no attribute 'from_elements'`, use the TLE-based constructor:

```python
sat = EarthSatellite(line1, line2, name, ts)
```

* **Column name mismatches**: Many merge errors stem from column names. `all_satellite_orbits.csv` uses `Satellite Name` and `Time (UTC)` by convention in this project. Ensure merges use the exact names or rename columns prior to merging:

```python
orbit_df.rename(columns={"Satellite Name": "Name", "Time (UTC)": "Timestamp"}, inplace=True)
```

* **Large CSVs**: `all_satellite_orbits.csv` can be huge (100s of MB). Don’t commit it to Git. Use `.gitignore` or Git LFS if needed. Keep working copies in `data/` and consider splitting by date or satellite for performance.

* **Plotly/Streamlit sizing**: If charts look small, ensure you use `st.plotly_chart(fig, use_container_width=True)` and that your CSS doesn't constrain the `.svg-container`.

* **Streamlit CLI not found**: Activate your venv first, then run `python -m streamlit run scripts/dashboard.py`. If `streamlit` is not installed into the environment, `pip install streamlit`.

---

# Git & large files guidelines

* `.gitignore` (recommended):

```
venv/
__pycache__/
*.pyc
.DS_Store
*.log
data/all_satellite_orbits.csv
data/persistent_risks.csv
data/persistent_risks_with_positions.csv
plots/
```

* If you must store large CSVs, use **Git LFS** or keep data in external storage (Google Drive / S3) and reference a download script.

* When the remote rejects pushes (merge conflicts), do:

```bash
git pull --rebase origin main
# resolve conflicts if any
git add .
git commit -m "Resolve merge conflicts"
git push
```

If your branch has no upstream yet:

```bash
git push --set-upstream origin main
```

---

# Next steps & recommended improvements

Short-term (high value):

* Train a **Risk Level classifier** (Random Forest / XGBoost) using `persistent_risks.csv`.
* Add **SHAP** explanations in the dashboard to explain model predictions.
* Add **persistence detection thresholds** and per-pair score/time-window alerting.
* Add **downloadable PDF reports** that summarize the top risks in a time window.

Medium-term:

* Time-series forecasting: use Prophet / LSTM to predict number of critical events in next 24 hours.
* Clustering satellites to detect groups with high interaction frequency.
* Deploy the dashboard (Streamlit Cloud / Heroku / Render) with scheduled data refresh.

Long-term:

* Integrate live TLE fetching from Celestrak / Space-Track and automate the pipeline.
* Build a decision-support system to recommend evasive maneuvers (RL research required).
* Expand to other catalogs (OneWeb, Iridium, GPS, debris catalogs).

---

# Contributing

1. Fork the repo.
2. Create a feature branch: `git checkout -b feat/my-feature`.
3. Add tests or small sample data if you change data processing.
4. Make a clear commit message and open a PR describing what changed and why.

If you want to add ML experiments, put experiments into a `notebooks/` folder and add a small README for reproducibility (including random seeds and environment).

---

# License & credits

* **Credits & Data Sources:**

  * Skyfield (for orbital computations)
  * Celestrak (Starlink / orbital metadata)
  * Plotly / Streamlit for visualization & UI

---
