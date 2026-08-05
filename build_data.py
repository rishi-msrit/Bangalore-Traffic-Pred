import os
import sys
import json
import warnings

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data.csv")
OUT_DIR   = os.path.join(BASE_DIR, "data")
os.makedirs(OUT_DIR, exist_ok=True)

def dump(name, obj):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  wrote {name}")

# ---------------------------------------------------------------
# Load and clean
# ---------------------------------------------------------------
raw = pd.read_csv(DATA_PATH)
df  = raw.copy()

df["Date"]                   = pd.to_datetime(df["Date"])
df["Area Name"]              = df["Area Name"].str.strip()
df["Road/Intersection Name"] = df["Road/Intersection Name"].str.strip()
df["Weather Conditions"]     = df["Weather Conditions"].str.strip()

df["DayOfWeek"] = df["Date"].dt.day_name()
df["Month"]     = df["Date"].dt.month
df["MonthName"] = df["Date"].dt.strftime("%b")
df["WeekType"]  = df["DayOfWeek"].apply(
    lambda d: "Weekend" if d in ["Saturday", "Sunday"] else "Weekday"
)

key_cols = ["Congestion Level", "Traffic Volume", "Average Speed",
            "Road/Intersection Name", "Area Name"]
df = df.dropna(subset=key_cols)

def classify_severity(level):
    if level < 50:   return "Low"
    if level < 75:   return "Moderate"
    if level < 90:   return "High"
    return "Critical"

df["Severity"] = df["Congestion Level"].apply(classify_severity)

# ---------------------------------------------------------------
# Shared derived values (mirrors main.py exactly)
# ---------------------------------------------------------------
WAIT_TIME_MIN  = 15
WAGE_PER_HOUR  = 150
FUEL_PER_IDLE  = 0.2
FUEL_PRICE     = 103

road_congestion      = df.groupby("Road/Intersection Name")["Congestion Level"].mean()
top5                 = road_congestion.nlargest(5)
top5_roads           = top5.index.tolist()
bot5_roads           = road_congestion.nsmallest(5).index.tolist()
city_avg             = df["Congestion Level"].mean()
city_speed_avg       = df["Average Speed"].mean()

avg_daily_vol        = (
    df.groupby(["Date", "Road/Intersection Name"])["Traffic Volume"]
    .mean().groupby(level=1).mean()
)
top5_daily_vol       = avg_daily_vol[top5_roads].sum()
wage_per_min         = WAGE_PER_HOUR / 60
productivity_per_veh = WAIT_TIME_MIN * wage_per_min
fuel_cost_per_veh    = FUEL_PER_IDLE * FUEL_PRICE
total_prod_loss      = productivity_per_veh * top5_daily_vol
total_fuel_loss      = fuel_cost_per_veh    * top5_daily_vol
grand_total          = total_prod_loss + total_fuel_loss

# ---------------------------------------------------------------
# kpis.json
# ---------------------------------------------------------------
print("Building kpis.json")

top5_avg        = top5.mean()
pct_critical    = (df["Severity"] == "Critical").mean() * 100
pct_full_cap    = (df["Road Capacity Utilization"] >= 99).mean() * 100
top5_speed_avg  = df[df["Road/Intersection Name"].isin(top5_roads)]["Average Speed"].mean()
bot5_speed_avg  = df[df["Road/Intersection Name"].isin(bot5_roads)]["Average Speed"].mean()
top5_vol_share  = (
    df[df["Road/Intersection Name"].isin(top5_roads)]["Traffic Volume"].sum()
    / df["Traffic Volume"].sum() * 100
)

severity_counts = df["Severity"].value_counts()
total_recs      = len(df)

inc_by_band = df.groupby(
    df["Congestion Level"].apply(lambda x: "high" if x > 75 else "low")
)["Incident Reports"].mean()

kpis = {
    "total_records":       total_recs,
    "date_range":          [df["Date"].min().strftime("%Y-%m-%d"),
                            df["Date"].max().strftime("%Y-%m-%d")],
    "city_avg_congestion": round(city_avg, 2),
    "city_avg_speed":      round(city_speed_avg, 1),
    "pct_critical":        round(pct_critical, 1),
    "pct_full_capacity":   round(pct_full_cap, 1),
    "top5_avg_congestion": round(top5_avg, 2),
    "top5_vs_city_pct":    round((top5_avg - city_avg) / city_avg * 100, 1),
    "top5_vol_share":      round(top5_vol_share, 1),
    "top5_speed_avg":      round(top5_speed_avg, 1),
    "bot5_speed_avg":      round(bot5_speed_avg, 1),
    "daily_loss_total":    round(grand_total),
    "daily_prod_loss":     round(total_prod_loss),
    "daily_fuel_loss":     round(total_fuel_loss),
    "severity_breakdown": {
        "Critical":  round(severity_counts.get("Critical",  0) / total_recs * 100, 1),
        "High":      round(severity_counts.get("High",      0) / total_recs * 100, 1),
        "Moderate":  round(severity_counts.get("Moderate",  0) / total_recs * 100, 1),
        "Low":       round(severity_counts.get("Low",       0) / total_recs * 100, 1),
    },
    "incident_ratio_high_vs_low": round(inc_by_band.get("high", 0) / max(inc_by_band.get("low", 1), 0.001), 1),
    "top5_roads": [
        {"name": road, "congestion": round(val, 1)}
        for road, val in top5.items()
    ],
}
dump("kpis.json", kpis)

# ---------------------------------------------------------------
# roads.json
# ---------------------------------------------------------------
print("Building roads.json")

roads_data = {}
cap_sat = (
    df.groupby("Road/Intersection Name")
    .apply(lambda g: (g["Road Capacity Utilization"] >= 99).mean() * 100,
           include_groups=False)
)

month_order = list(range(1, 13))
month_labels = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]

all_roads = sorted(df["Road/Intersection Name"].unique())

for road in all_roads:
    rdf        = df[df["Road/Intersection Name"] == road]
    sev_counts = rdf["Severity"].value_counts()
    recs       = len(rdf)

    monthly_cong = (
        rdf.groupby("Month")["Congestion Level"]
        .mean()
        .reindex(month_order)
        .fillna(None)
    )

    roads_data[road] = {
        "area":             rdf["Area Name"].iloc[0],
        "is_top5":          road in top5_roads,
        "mean_congestion":  round(road_congestion[road], 2),
        "mean_speed":       round(rdf["Average Speed"].mean(), 1),
        "capacity_sat_pct": round(cap_sat[road], 1),
        "incident_rate":    round(rdf["Incident Reports"].mean(), 2),
        "daily_vol":        round(avg_daily_vol.get(road, 0), 0),
        "vs_city_avg":      round(road_congestion[road] - city_avg, 2),
        "severity_pct": {
            "Critical": round(sev_counts.get("Critical", 0) / recs * 100, 1),
            "High":     round(sev_counts.get("High",     0) / recs * 100, 1),
            "Moderate": round(sev_counts.get("Moderate", 0) / recs * 100, 1),
            "Low":      round(sev_counts.get("Low",      0) / recs * 100, 1),
        },
        "monthly_congestion": {
            "labels": month_labels,
            "values": [
                round(v, 2) if v is not None and not np.isnan(v) else None
                for v in monthly_cong.values
            ],
        },
    }

dump("roads.json", roads_data)

# ---------------------------------------------------------------
# heatmap.json
# ---------------------------------------------------------------
print("Building heatmap.json")

day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
pivot = (
    df.groupby(["DayOfWeek", "Road/Intersection Name"])["Congestion Level"]
    .mean()
    .unstack(fill_value=0)
    .reindex(day_order)
)

heatmap = {
    "days":  day_order,
    "roads": list(pivot.columns),
    "values": [
        [round(v, 1) for v in row]
        for row in pivot.values.tolist()
    ],
}
dump("heatmap.json", heatmap)

# ---------------------------------------------------------------
# weather.json
# ---------------------------------------------------------------
print("Building weather.json")

weather_cong  = df.groupby("Weather Conditions")["Congestion Level"].mean()
weather_count = df["Weather Conditions"].value_counts()
clear_avg     = weather_cong["Clear"]

weather = {
    "clear_baseline": round(float(clear_avg), 2),
    "conditions": [
        {
            "condition": w,
            "mean_congestion": round(float(weather_cong[w]), 2),
            "delta_vs_clear":  round(float(weather_cong[w] - clear_avg), 2),
            "record_count":    int(weather_count.get(w, 0)),
        }
        for w in weather_cong.sort_values(ascending=False).index
    ],
    "finding": "Congestion is structural, not weather-driven. Rain and Overcast are below the Clear baseline.",
}
dump("weather.json", weather)

# ---------------------------------------------------------------
# economic.json
# ---------------------------------------------------------------
print("Building economic.json")

per_road_daily_vol  = avg_daily_vol[top5_roads]
per_road_prod_loss  = per_road_daily_vol * productivity_per_veh
per_road_fuel_loss  = per_road_daily_vol * fuel_cost_per_veh
per_road_total      = per_road_prod_loss + per_road_fuel_loss

economic = {
    "assumptions": {
        "wait_time_min":   WAIT_TIME_MIN,
        "wage_per_hour":   WAGE_PER_HOUR,
        "fuel_per_idle_l": FUEL_PER_IDLE,
        "fuel_price":      FUEL_PRICE,
    },
    "per_vehicle": {
        "productivity_loss": round(productivity_per_veh, 2),
        "fuel_loss":         round(fuel_cost_per_veh, 2),
    },
    "totals": {
        "daily_vol_top5":  round(top5_daily_vol),
        "prod_loss":       round(total_prod_loss),
        "fuel_loss":       round(total_fuel_loss),
        "grand_total":     round(grand_total),
    },
    "per_road": [
        {
            "road":      road,
            "daily_vol": round(per_road_daily_vol[road]),
            "prod_loss": round(per_road_prod_loss[road]),
            "fuel_loss": round(per_road_fuel_loss[road]),
            "total":     round(per_road_total[road]),
        }
        for road in per_road_total.sort_values(ascending=False).index
    ],
}
dump("economic.json", economic)

# ---------------------------------------------------------------
# correlation.json
# ---------------------------------------------------------------
print("Building correlation.json")

numeric_cols = [
    "Traffic Volume", "Average Speed", "Travel Time Index",
    "Congestion Level", "Road Capacity Utilization",
    "Incident Reports", "Environmental Impact",
    "Public Transport Usage", "Traffic Signal Compliance",
    "Parking Usage", "Pedestrian and Cyclist Count",
]

corr_matrix = df[numeric_cols].corr().round(3)

correlation = {
    "columns": numeric_cols,
    "matrix":  corr_matrix.values.tolist(),
}
dump("correlation.json", correlation)

# ---------------------------------------------------------------
# model.json  (linear regression, single model)
# ---------------------------------------------------------------
print("Building model.json")

feature_cols = [
    "Traffic Volume", "Average Speed", "Travel Time Index",
    "Road Capacity Utilization", "Incident Reports",
    "Environmental Impact", "Public Transport Usage",
    "Traffic Signal Compliance", "Parking Usage",
    "Pedestrian and Cyclist Count",
]

model_df  = df[feature_cols + ["Congestion Level"]].dropna()
X         = model_df[feature_cols].values
y         = model_df["Congestion Level"].values

scaler    = StandardScaler()
X_scaled  = scaler.fit_transform(X)

reg       = LinearRegression()
reg.fit(X_scaled, y)
y_pred    = reg.predict(X_scaled)

ss_res    = np.sum((y - y_pred) ** 2)
ss_tot    = np.sum((y - y.mean()) ** 2)
r2        = 1 - ss_res / ss_tot
mae       = mean_absolute_error(y, y_pred)

coef_pairs = sorted(
    zip(feature_cols, reg.coef_),
    key=lambda x: abs(x[1]),
    reverse=True,
)

model = {
    "target":   "Congestion Level",
    "features": feature_cols,
    "r2":       round(r2, 4),
    "mae":      round(mae, 4),
    "intercept": round(float(reg.intercept_), 4),
    "coefficients": [
        {"feature": f, "coef": round(float(c), 4)}
        for f, c in coef_pairs
    ],
    "interpretation": {
        "r2":  "Proportion of variance in Congestion Level explained by the model. Higher is better (max 1.0).",
        "mae": "Average absolute prediction error in congestion-level units (0-100 scale).",
    },
}
dump("model.json", model)

# ---------------------------------------------------------------
# clusters.json  (K-means, k=4)
# ---------------------------------------------------------------
print("Building clusters.json")

road_features = df.groupby("Road/Intersection Name").agg(
    mean_congestion       = ("Congestion Level", "mean"),
    mean_speed            = ("Average Speed", "mean"),
    capacity_sat          = ("Road Capacity Utilization", lambda s: (s >= 99).mean()),
    incident_rate         = ("Incident Reports", "mean"),
    traffic_vol           = ("Traffic Volume", "mean"),
    travel_time_idx       = ("Travel Time Index", "mean"),
).reset_index()

feat_for_cluster = [
    "mean_congestion", "mean_speed", "capacity_sat",
    "incident_rate", "traffic_vol", "travel_time_idx",
]
Xc       = road_features[feat_for_cluster].values
sc2      = StandardScaler()
Xc_s     = sc2.fit_transform(Xc)

km       = KMeans(n_clusters=4, random_state=42, n_init=10)
labels   = km.fit_predict(Xc_s)

pca      = PCA(n_components=2, random_state=42)
coords   = pca.fit_transform(Xc_s)

cluster_names = {
    # assigned after inspecting cluster center means
}
# Build cluster descriptors from center stats
centers_orig = sc2.inverse_transform(km.cluster_centers_)
center_df    = pd.DataFrame(centers_orig, columns=feat_for_cluster)

def describe_cluster(row):
    cong = row["mean_congestion"]
    if cong >= 88:  return "Severe Chokepoint"
    if cong >= 82:  return "High-Congestion Corridor"
    if cong >= 72:  return "Moderate-Flow Road"
    return "Relatively Clear Road"

descriptors = [describe_cluster(center_df.iloc[i]) for i in range(4)]

clusters = {
    "roads": [
        {
            "road":        road_features.iloc[i]["Road/Intersection Name"],
            "cluster":     int(labels[i]),
            "descriptor":  descriptors[int(labels[i])],
            "pca_x":       round(float(coords[i, 0]), 4),
            "pca_y":       round(float(coords[i, 1]), 4),
            "mean_congestion": round(float(road_features.iloc[i]["mean_congestion"]), 2),
            "mean_speed":      round(float(road_features.iloc[i]["mean_speed"]), 1),
        }
        for i in range(len(road_features))
    ],
    "cluster_descriptors": descriptors,
    "explained_variance":  [round(float(v), 4) for v in pca.explained_variance_ratio_],
}
dump("clusters.json", clusters)

# ---------------------------------------------------------------
# anomalies.json  (z-score > 2.5 per road baseline)
# ---------------------------------------------------------------
print("Building anomalies.json")

anomaly_records = []
Z_THRESHOLD = 2.5

for road in all_roads:
    rdf     = df[df["Road/Intersection Name"] == road].copy()
    mu      = rdf["Congestion Level"].mean()
    sigma   = rdf["Congestion Level"].std()
    if sigma == 0:
        continue
    rdf["z"] = (rdf["Congestion Level"] - mu) / sigma
    spikes   = rdf[rdf["z"] > Z_THRESHOLD].sort_values("z", ascending=False)
    for _, row in spikes.iterrows():
        anomaly_records.append({
            "road":       road,
            "date":       row["Date"].strftime("%Y-%m-%d"),
            "congestion": round(row["Congestion Level"], 1),
            "z_score":    round(row["z"], 2),
            "weather":    row["Weather Conditions"],
            "day":        row["DayOfWeek"],
        })

anomaly_records.sort(key=lambda x: x["z_score"], reverse=True)

anomalies = {
    "threshold_z": Z_THRESHOLD,
    "total_flags": len(anomaly_records),
    "records":     anomaly_records,
}
dump("anomalies.json", anomalies)

# ---------------------------------------------------------------
# monthly_trend.json
# ---------------------------------------------------------------
print("Building monthly_trend.json")

monthly_overall = (
    df.groupby("Month")["Congestion Level"].mean()
    .reindex(month_order).fillna(None)
)
monthly_wd = (
    df[df["WeekType"] == "Weekday"].groupby("Month")["Congestion Level"].mean()
    .reindex(month_order).fillna(None)
)
monthly_we = (
    df[df["WeekType"] == "Weekend"].groupby("Month")["Congestion Level"].mean()
    .reindex(month_order).fillna(None)
)

def safe_round(v):
    if v is None: return None
    try:
        if np.isnan(v): return None
        return round(float(v), 2)
    except Exception:
        return None

monthly_trend = {
    "labels":   month_labels,
    "overall":  [safe_round(v) for v in monthly_overall],
    "weekday":  [safe_round(v) for v in monthly_wd],
    "weekend":  [safe_round(v) for v in monthly_we],
    "city_avg": round(city_avg, 2),
}
dump("monthly_trend.json", monthly_trend)

print("\nDone. All JSON files written to:", OUT_DIR)
