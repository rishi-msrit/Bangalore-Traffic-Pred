# Bangalore Traffic Pattern Analysis

Dataset: [Bangalore Traffic Pulse — Kaggle](https://www.kaggle.com/datasets/preethamgouda/banglore-city-traffic-dataset) | Records: 8,936 | Period: Jan 2022 – Aug 2024

## Dataset Description

| Field | Description |
|---|---|
| `Date` | Observation date (2022–2024) |
| `Area Name` | One of 8 Bangalore zones |
| `Road/Intersection Name` | One of 16 specific roads |
| `Traffic Volume` | Vehicle count at the location |
| `Average Speed` | Speed in km/h |
| `Congestion Level` | 0–100 scale (100 = fully blocked) |
| `Road Capacity Utilization` | % of road capacity in use |
| `Incident Reports` | Number of incidents recorded |
| `Weather Conditions` | Clear / Fog / Rain / Windy / Overcast |

---

## Steps Performed

| Sr No | Description |
|---|---|
| `1` | Load raw: data shape, columns, dtypes |
| `2` | Data cleaning: parse dates, strip whitespace, check nulls, add time features |
| `3` | EDA  descriptive: stats + correlation with Congestion Level |
| `4` | Top 5 Chokepoints: ranked by mean Congestion Level |
| `5` | Economic Impact: productivity loss + fuel waste (₹/day) |
| `6`| Speed Analysis: average speed per road, chokepoints highlighted |
| `7` | Capacity Saturation: % of time each road runs at 100% capacity |
| `8` | Incident Frequency: high vs low congestion zone comparison |
| `9` | Plot: Economic impact stacked bar (per road) |
| `10` | Plot: Top 5 chokepoints vs city average (bar chart) |
| `11` | Plot: Congestion heatmap — Day of Week × Road |
| `12` | Plot: Monthly trend — Weekday vs Weekend (2022–2024) |
| `13` | Plot: Average speed per road — all 16 roads |
| `14` | Plot: Weather conditions vs congestion level |
| `15` | Congestion Severity Classification: 4-band breakdown |
| `16` | Final summary printout |


---

## Results & Visualizations

<div align="center">

<img src="images/economic_impact.png" width="75%"/>
<br>
<img src="images/top5_chokepoints.png" width="75%"/>
<br>
<img src="images/heatmap_day_road.png" width="75%"/>
<br>
<img src="images/monthly_trend.png" width="75%"/>
<br>
<img src="images/speed_per_road.png" width="75%"/>
<br>
<img src="images/weather_impact.png" width="75%"/>
</div>

---
## Key Findings

### Chokepoints
- **Top 5:** Sony World Junction (94.1), Sarjapur Road (93.8), Anil Kumble Circle (90.8), Trinity Circle (90.4), CMH Road (88.2)
- Top 5 average congestion: **91.5 / 100**, which is **13.2% above the city average of 80.8**
- These 5 roads carry **52.3% of total traffic volume**

### Speed
- City-wide average speed: **39.4 km/h**
- Top 5 chokepoints average speed: **37.3 km/h**
- Worst road — Sony World Junction: **36.0 km/h**
- Least congested roads average: **43.2 km/h** (19% faster)

### Severity
- **52.3% of all 8,936 observations** fall in the Critical (>90) congestion band
- Sony World Junction is in Critical state **87% of the time**

### Capacity Saturation
- **74.2% of all observations** show roads operating at 100% capacity
- Top 5 chokepoints are at full capacity **89.8% of the time** — this is structural overload, not just peak-hour congestion
- Least congested roads hit full capacity only **40.8% of the time**

### Incidents
- High-congestion zones (>75) record **2.9× more incidents** than low-congestion zones
- Top 5 roads: avg **1.83 incidents/record** vs **1.03** at the 5 least congested roads

### Economic Impact
*(15-min avg delay, ₹150/hr wage, ₹103/litre petrol — stated assumptions)*
- Productivity loss per vehicle: **₹37.50**
- Fuel waste per vehicle: **₹20.60**
- Estimated daily vehicles at top 5: **~1.85 lakh**
- **Total estimated daily loss: ₹1.07 crore** (₹69.3L productivity + ₹38.1L fuel)

### Weather
- Windy weather produces the highest congestion: **82.37** (+1.65 vs Clear baseline of 80.72)
- Rain and Overcast are marginally *below* the Clear baseline — suggesting congestion is structural, not weather-driven

---

## Assumptions Used

| Assumption | Value | Basis |
|---|---|---|
| Average delay at chokepoint | 15 minutes | Project specification |
| Average hourly wage (Bangalore) | ₹150/hr | ₹30,000/month ÷ 200 working hours |
| Fuel wasted during 15-min idle | 0.2 litres | Standard petrol car estimate |
| Petrol price | ₹103/litre | Bangalore approximate price (2024) |
| "Full capacity" threshold | ≥ 99% utilization | Dataset-based |
| "High congestion" threshold | Congestion Level > 75 | Dataset-based classification |

---

## How to Run

```bash
pip install pandas matplotlib
python -X utf8 main.py
```

> The `-X utf8` flag ensures the ₹ symbol prints correctly on Windows.

---

## Interactive Web Layer

**Live site:** [link to be added after Vercel deployment]

A static, no-backend interactive website built on top of the same dataset and analysis. All computation runs once offline in Python (`build_data.py`), results are exported to structured JSON files, and the site reads those files client-side at load time using `fetch()`. No server, no live backend, no API.

### Why this architecture

The underlying data does not change in real time. Running computation once and serving static JSON is faster, cheaper (free on Vercel), and more portable than maintaining a live backend. This is a standard pattern for dashboards built on fixed datasets.

### Pages

| Page | Audience | What it shows |
|---|---|---|
| Overview | General | City-wide KPI strip, top-5 chokepoints bar, severity distribution, all-roads speed comparison |
| Road Explorer | General | Per-road profile: monthly congestion trend vs city average, severity breakdown, speed, capacity saturation, incident rate |
| Patterns | General | Day-of-week x road congestion heatmap, weekday vs weekend monthly trend, weather-impact bar chart |
| Economic Impact | General | Rs 1.07 crore/day breakdown by road and by cost type (productivity vs fuel), assumptions displayed |
| Technical | Analysts | Full correlation matrix, linear regression coefficients and metrics (R2, MAE), k-means road clustering PCA scatter, anomaly flag table |

### Project structure (new files)

```
build_data.py          offline computation script (run once to regenerate data/)
data/                  generated JSON files consumed by the site
  kpis.json
  roads.json
  heatmap.json
  weather.json
  economic.json
  correlation.json
  model.json
  clusters.json
  anomalies.json
  monthly_trend.json
web/                   static site (HTML, CSS, vanilla JS)
  index.html
  explorer.html
  patterns.html
  impact.html
  technical.html
  css/style.css
  js/theme.js          light/dark mode toggle
  js/info.js           reusable info tooltip component
vercel.json            Vercel routing config
```

### How to run locally

```bash
pip install pandas scikit-learn numpy
python -X utf8 build_data.py
python -m http.server 8765
```

Then open `http://localhost:8765/web/index.html` in a browser.

### How to regenerate data

If `data.csv` is updated, run `build_data.py` again. It overwrites all JSON files in `data/` and does not touch `main.py` or any other existing file.

### Deploying to Vercel

Connect the repo to Vercel. The `vercel.json` at the repo root handles routing so that `/web/` pages and `/data/` JSON files are both accessible from the same deployment.

### Screenshots

[to be added after deployment]

---
