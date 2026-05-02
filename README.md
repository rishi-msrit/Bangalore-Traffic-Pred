# Bangalore Traffic Pattern Analysis

Dataset: [Bangalore Traffic Pulse — Kaggle](https://www.kaggle.com/datasets/preethamgouda/banglore-city-traffic-dataset) | Records: 8,936 | Period: Jan 2022 – Aug 2024

---

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
 
|---|---|
| `1` | Load raw data — shape, columns, dtypes |
| `2` | Data cleaning — parse dates, strip whitespace, check nulls, add time features |
| `3` | EDA — descriptive stats + correlation with Congestion Level |
| `4` | Top 5 Chokepoints — ranked by mean Congestion Level |
| `5` | Economic Impact — productivity loss + fuel waste (₹/day) |
| `6`| Speed Analysis — average speed per road, chokepoints highlighted |
| `7` | Capacity Saturation — % of time each road runs at 100% capacity |
| `8` | Incident Frequency — high vs low congestion zone comparison |
| `9` | Plot: Economic impact stacked bar (per road) |
| `10` | Plot: Top 5 chokepoints vs city average (bar chart) |
| `11` | Plot: Congestion heatmap — Day of Week × Road |
| `12` | Plot: Monthly trend — Weekday vs Weekend (2022–2024) |
| `13` | Plot: Average speed per road — all 16 roads |
| `14` | Plot: Weather conditions vs congestion level |
| `15` | Congestion Severity Classification — 4-band breakdown |
| `16` | Final summary printout |

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

## Output Files

```
images/
├── economic_impact.png     ← Stacked bar: productivity + fuel loss per road
├── top5_chokepoints.png    ← Top 5 roads vs city average
├── heatmap_day_road.png    ← Day of Week × Road congestion heatmap
├── monthly_trend.png       ← Weekday vs Weekend trend (2022–2024)
├── speed_per_road.png      ← Average speed: all 16 roads, chokepoints highlighted
└── weather_impact.png      ← Weather condition vs mean congestion
```
## How to Run

```bash
pip install pandas matplotlib
python -X utf8 main.py
```

> The `-X utf8` flag ensures the ₹ symbol prints correctly on Windows.

---
