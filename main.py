import os
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_PATH   = os.path.join(BASE_DIR, "data.csv")
IMAGES_DIR  = os.path.join(BASE_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# STEP 1 — LOAD DATA 
print("=" * 60)
print("STEP 1 : Loading & Inspecting Data")
print("=" * 60)

raw_df = pd.read_csv(DATA_PATH)
print(f"  Rows   : {raw_df.shape[0]:,}")
print(f"  Columns: {raw_df.shape[1]}")
print(f"  Columns: {raw_df.columns.tolist()}")

# STEP 2 — CLEAN DATA 
print("\n" + "=" * 60)
print("STEP 2 : Data Cleaning  (original data.csv untouched)")
print("=" * 60)

df = raw_df.copy()                         

df["Date"] = pd.to_datetime(df["Date"])

# Striping whitespace 
df["Area Name"]             = df["Area Name"].str.strip()
df["Road/Intersection Name"] = df["Road/Intersection Name"].str.strip()
df["Weather Conditions"]    = df["Weather Conditions"].str.strip()

# Addin useful time features
df["DayOfWeek"]  = df["Date"].dt.day_name()
df["Month"]      = df["Date"].dt.month
df["MonthName"]  = df["Date"].dt.strftime("%b")
df["WeekType"]   = df["DayOfWeek"].apply(
    lambda d: "Weekend" if d in ["Saturday", "Sunday"] else "Weekday"
)

#(missing value check logic)
missing = df.isnull().sum()
if missing.sum() == 0:
    print("  No missing values found — dataset is clean.")
else:
    print("  Missing values detected:")
    print(missing[missing > 0])
    key_cols = ["Congestion Level", "Traffic Volume", "Average Speed",
                "Road/Intersection Name", "Area Name"]
    before = len(df)
    df = df.dropna(subset=key_cols)
    print(f"  Dropped {before - len(df)} rows with nulls in key columns.")

print(f"  Working dataset: {len(df):,} rows")

# (printed summary)
print("\n" + "=" * 60)
print("STEP 3 : Basic Exploratory Data Analysis")
print("=" * 60)

numeric_cols = ["Traffic Volume", "Average Speed",
                "Congestion Level", "Road Capacity Utilization",
                "Travel Time Index", "Incident Reports"]

print("\n  Descriptive Statistics:")
print(df[numeric_cols].describe().round(2).to_string())

print("\n  Correlation with Congestion Level:")
corr = df[numeric_cols].corr()["Congestion Level"].drop("Congestion Level")
for col, val in corr.sort_values(ascending=False).items():
    print(f"    {col:<30} : {val:+.3f}")

# TOP 5 CHOKEPOINTS
print("\n" + "=" * 60)
print("STEP 4 : Identifying Top 5 Chokepoints")
print("=" * 60)

road_congestion = (
    df.groupby("Road/Intersection Name")["Congestion Level"]
    .mean()
    .sort_values(ascending=False)
)

top5 = road_congestion.head(5)
city_avg = df["Congestion Level"].mean()
top5_avg = top5.mean()
pct_diff = (top5_avg - city_avg) / city_avg * 100

print(f"\n  City-wide average congestion : {city_avg:.2f} / 100")
print(f"  Top-5 chokepoints average    : {top5_avg:.2f} / 100")
print(f"  Chokepoints vs city average  : +{pct_diff:.1f}%")

print("\n  Top 5 Chokepoints (Mean Congestion Level):")
print("  " + "-" * 45)
for rank, (road, val) in enumerate(top5.items(), start=1):
    diff = val - city_avg
    print(f"  #{rank}  {road:<28}  {val:.2f}  (+{diff:.2f} above avg)")
print("  " + "-" * 45)

area_congestion = (
    df.groupby("Area Name")["Congestion Level"]
    .mean()
    .sort_values(ascending=False)
)
print("\n  Congestion by Area (all 8 areas):")
for area, val in area_congestion.items():
    print(f"    {area:<20} : {val:.2f}")

#  LOST PRODUCTIVITY & ECONOMIC IMPACT
print("\n" + "=" * 60)
print("STEP 5 : Productivity Loss & Economic Impact Estimate")
print("=" * 60)

# Assumptions as the dataset has some missing data,like avg wait time 
WAIT_TIME_MIN   = 15        # minutes average wait at a chokepoint
WAGE_PER_HOUR   = 150       # rupee/hr — Bangalore median income ~₹30,000/mo ÷ 200 hrs
FUEL_PER_IDLE   = 0.2       # litres wasted per 15-min idle 
FUEL_PRICE      = 103       # rupee/litre 

# Average daily traffic volume across all 16 roads
avg_daily_vol_per_road = df.groupby(
    ["Date", "Road/Intersection Name"]
)["Traffic Volume"].mean().groupby(level=1).mean()

top5_roads = top5.index.tolist()
top5_daily_vol = avg_daily_vol_per_road[top5_roads].sum()

# Productivity loss
wage_per_min          = WAGE_PER_HOUR / 60
productivity_per_veh  = WAIT_TIME_MIN * wage_per_min
total_prod_loss       = productivity_per_veh * top5_daily_vol  

# Fuel loss
fuel_cost_per_veh = FUEL_PER_IDLE * FUEL_PRICE              
total_fuel_loss   = fuel_cost_per_veh * top5_daily_vol       

grand_total = total_prod_loss + total_fuel_loss

print(f"\n  Assumptions used:")
print(f"    Average wait time per vehicle  : {WAIT_TIME_MIN} minutes")
print(f"    Average hourly wage (Bangalore): ₹{WAGE_PER_HOUR}/hour")
print(f"    Fuel wasted (15-min idle)      : {FUEL_PER_IDLE} litres/vehicle")
print(f"    Petrol price                   : ₹{FUEL_PRICE}/litre")

print(f"\n  Dataset-derived values:")
print(f"    Estimated daily vehicles at top-5 chokepoints: {top5_daily_vol:,.0f}")

print(f"\n  ┌─────────────────────────────────────────────────────┐")
print(f"  │  Productivity loss per vehicle  : ₹{productivity_per_veh:.2f}           │")
print(f"  │  Fuel loss per vehicle          : ₹{fuel_cost_per_veh:.2f}           │")
print(f"  ├─────────────────────────────────────────────────────┤")
print(f"  │  Total productivity loss / day  : ₹{total_prod_loss:,.0f}       │")
print(f"  │  Total fuel loss / day          : ₹{total_fuel_loss:,.0f}       │")
print(f"  ├─────────────────────────────────────────────────────┤")
print(f"  │  GRAND TOTAL DAILY IMPACT       : ₹{grand_total:,.0f}       │")
print(f"  └─────────────────────────────────────────────────────┘")

#AVERAGE SPEED PER ROAD
print("\n" + "=" * 60)
print("STEP 6 : Average Speed Analysis per Road")
print("=" * 60)

speed_per_road = (
    df.groupby("Road/Intersection Name")["Average Speed"]
    .mean()
    .sort_values()
)

city_speed_avg = df["Average Speed"].mean()
top5_speed     = df[df["Road/Intersection Name"].isin(top5_roads)]["Average Speed"].mean()
bot5_roads     = road_congestion.tail(5).index.tolist()   # least congested
bot5_speed     = df[df["Road/Intersection Name"].isin(bot5_roads)]["Average Speed"].mean()
speed_drop_pct = (city_speed_avg - top5_speed) / city_speed_avg * 100

print(f"\n  City-wide average speed      : {city_speed_avg:.1f} km/h")
print(f"  Top-5 congested roads avg    : {top5_speed:.1f} km/h")
print(f"  Bottom-5 (clear) roads avg   : {bot5_speed:.1f} km/h")
print(f"  Speed drop at chokepoints    : {speed_drop_pct:.1f}% below city average")

print("\n  Speed ranking (slowest → fastest):")
for road, spd in speed_per_road.items():
    marker = " ◄ CHOKEPOINT" if road in top5_roads else ""
    print(f"    {road:<28} : {spd:.1f} km/h{marker}")

# Plot: horizontal bar — all roads by avg speed, chokepoints highlighted
fig, ax = plt.subplots(figsize=(10, 6))

bar_colors = ["#c0392b" if road in top5_roads else "#3498db"
              for road in speed_per_road.index]
bars = ax.barh(speed_per_road.index, speed_per_road.values,
               color=bar_colors, edgecolor="white", height=0.6)

# City average reference
ax.axvline(city_speed_avg, color="#2c3e50", linestyle="--", linewidth=1.5,
           label=f"City Average: {city_speed_avg:.1f} km/h")

# Value labels
for bar, val in zip(bars, speed_per_road.values):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}", va="center", fontsize=9)

# Custom legend
from matplotlib.patches import Patch
legend_handles = [
    Patch(color="#c0392b", label="Top-5 Chokepoint"),
    Patch(color="#3498db", label="Other Roads"),
    plt.Line2D([0], [0], color="#2c3e50", linestyle="--",
               label=f"City Average: {city_speed_avg:.1f} km/h")
]
ax.legend(handles=legend_handles, fontsize=9, loc="lower right")
ax.set_xlabel("Average Speed (km/h)", fontsize=11)
ax.set_title("Average Vehicle Speed by Road — Bangalore\n"
             "(Red = Top 5 Congested Roads)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlim(0, 56)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()

save_path = os.path.join(IMAGES_DIR, "speed_per_road.png")
plt.savefig(save_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"\n  Saved → {save_path}")

# ROAD CAPACITY SATURATION
print("\n" + "=" * 60)
print("STEP 7 : Road Capacity Saturation Analysis")
print("=" * 60)

cap_sat = (
    df.groupby("Road/Intersection Name")
    .apply(lambda g: (g["Road Capacity Utilization"] >= 99).mean() * 100,
           include_groups=False)
    .sort_values(ascending=False)
)

overall_sat_pct = (df["Road Capacity Utilization"] >= 99).mean() * 100
print(f"\n  City-wide: {overall_sat_pct:.1f}% of all observations at 100% road capacity")
print(f"  This means roads are STRUCTURALLY SATURATED — not just peak-hour congestion.")

print("\n  % of time each road operates at full capacity:")
print("  " + "-" * 45)
for road, pct in cap_sat.items():
    bar  = "█" * int(pct / 5)
    flag = " ◄" if road in top5_roads else ""
    print(f"  {road:<28} : {pct:.1f}%  {bar}{flag}")
print("  " + "-" * 45)

top5_cap_avg = cap_sat[top5_roads].mean()
bot5_cap_avg = cap_sat[bot5_roads].mean()
print(f"\n  Top-5 chokepoints at full capacity: {top5_cap_avg:.1f}% of the time")
print(f"  Bottom-5 roads at full capacity   : {bot5_cap_avg:.1f}% of the time")

#  INCIDENT FREQUENCY ANALYSIS
print("\n" + "=" * 60)
print("STEP 8 : Incident Frequency at High vs Low Congestion Zones")
print("=" * 60)

# Tag records as high / low congestion
df["CongBand"] = df["Congestion Level"].apply(
    lambda x: "High (>75)" if x > 75 else "Low (≤75)"
)

# Average incidents per band
inc_by_band = df.groupby("CongBand")["Incident Reports"].mean()
inc_ratio   = inc_by_band["High (>75)"] / inc_by_band["Low (≤75)"]

print(f"\n  Avg incidents — High congestion (>75) : {inc_by_band['High (>75)']:.2f} per record")
print(f"  Avg incidents — Low congestion (≤75)  : {inc_by_band['Low (≤75)']:.2f} per record")
print(f"  High-congestion zones see {inc_ratio:.1f}x more incidents than low-congestion zones")

top5_inc = df[df["Road/Intersection Name"].isin(top5_roads)]["Incident Reports"].mean()
bot5_inc  = df[df["Road/Intersection Name"].isin(bot5_roads)]["Incident Reports"].mean()
print(f"\n  Top-5 chokepoints avg incidents  : {top5_inc:.2f}")
print(f"  Bottom-5 roads avg incidents     : {bot5_inc:.2f}")
print(f"  Ratio: {top5_inc / bot5_inc:.1f}x more incidents at major chokepoints")

# PLOTS

print("\n" + "=" * 60)
print("STEP 6 : Plot 1 — Daily Economic Impact (Stacked Bar)")
print("=" * 60)

# Per-road daily traffic volume (from dataset)
per_road_daily_vol = avg_daily_vol_per_road[top5_roads]

# Per-road cost breakdown
per_road_prod_loss = per_road_daily_vol * productivity_per_veh   # ₹ / day
per_road_fuel_loss = per_road_daily_vol * fuel_cost_per_veh      # ₹ / day
per_road_total     = per_road_prod_loss + per_road_fuel_loss

# Sort by total impact (highest at top for horizontal bar)
sort_order = per_road_total.sort_values(ascending=True).index
prod_sorted = per_road_prod_loss[sort_order] / 1e5   # convert to lakh ₹
fuel_sorted = per_road_fuel_loss[sort_order] / 1e5
total_sorted = per_road_total[sort_order] / 1e5

fig, ax = plt.subplots(figsize=(11, 5))

bars_prod = ax.barh(sort_order, prod_sorted.values,
                    color="#e74c3c", label="Productivity Loss", height=0.55)
bars_fuel = ax.barh(sort_order, fuel_sorted.values,
                    left=prod_sorted.values,
                    color="#e67e22", label="Fuel Cost", height=0.55)

# Total label at end of each bar
for i, (road, total) in enumerate(total_sorted.items()):
    ax.text(total + 0.3, i, f"₹{total:.1f}L", va="center",
            fontsize=10, fontweight="bold", color="#2c3e50")

# Grand total annotation
ax.axvline(grand_total / 1e5, color="#2c3e50", linestyle="--",
           linewidth=1.5, label=f"Grand Total: ₹{grand_total/1e5:.1f}L/day")

ax.set_xlabel("Estimated Daily Economic Loss (₹ Lakh)", fontsize=11)
ax.set_title("Daily Economic Loss per Chokepoint — Bangalore\n"
             "(Productivity Loss + Fuel Waste, 15-min avg delay assumed)",
             fontsize=13, fontweight="bold", pad=12)
ax.legend(fontsize=10)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()

save_path = os.path.join(IMAGES_DIR, "economic_impact.png")
plt.savefig(save_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved → {save_path}")

print("\n" + "=" * 60)
print("STEP 7 : Plot 2 — Top 5 Chokepoints Bar Chart")
print("=" * 60)

fig, ax = plt.subplots(figsize=(10, 5))

colors = ["#c0392b" if v == top5.max() else "#e74c3c" for v in top5.values]
bars   = ax.barh(top5.index[::-1], top5.values[::-1], color=colors[::-1],
                 edgecolor="white", height=0.6)

# City average line
ax.axvline(city_avg, color="#2c3e50", linestyle="--", linewidth=1.5,
           label=f"City Average: {city_avg:.1f}")

# Value labels on bars
for bar, val in zip(bars, top5.values[::-1]):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}", va="center", fontsize=10, fontweight="bold")

ax.set_xlabel("Mean Congestion Level (0–100)", fontsize=11)
ax.set_title("Top 5 Traffic Chokepoints in Bangalore\n(by Mean Congestion Level)",
             fontsize=13, fontweight="bold", pad=12)
ax.legend(fontsize=10)
ax.set_xlim(0, 105)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()

save_path = os.path.join(IMAGES_DIR, "top5_chokepoints.png")
plt.savefig(save_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved → {save_path}")

print("\n" + "=" * 60)
print("STEP 8 : Plot 3 — Heatmap (Day of Week × Location)")
print("=" * 60)

# Build pivot: rows = day of week, cols = road name
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]

pivot = (
    df.groupby(["DayOfWeek", "Road/Intersection Name"])["Congestion Level"]
    .mean()
    .unstack(fill_value=0)
)
pivot = pivot.reindex(day_order)           # order days Mon→Sun

fig, ax = plt.subplots(figsize=(14, 5))
im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn_r", vmin=60, vmax=100)

# Axes labels
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns, rotation=40, ha="right", fontsize=9)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index, fontsize=10)

# Annotate each cell with the value
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        val = pivot.values[i, j]
        ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                fontsize=8, color="black" if val < 85 else "white")

plt.colorbar(im, ax=ax, label="Mean Congestion Level")
ax.set_title("Congestion Heatmap — Day of Week × Road/Intersection",
             fontsize=13, fontweight="bold", pad=12)
plt.tight_layout()

save_path = os.path.join(IMAGES_DIR, "heatmap_day_road.png")
plt.savefig(save_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved → {save_path}")

print("\n" + "=" * 60)
print("STEP 9 : Plot 4 — Monthly Congestion Trend")
print("=" * 60)

month_order   = list(range(1, 13))
month_labels  = ["Jan","Feb","Mar","Apr","May","Jun",
                 "Jul","Aug","Sep","Oct","Nov","Dec"]

monthly = (
    df.groupby("Month")["Congestion Level"]
    .mean()
    .reindex(month_order)
)

# Split weekday vs weekend
monthly_wd = (
    df[df["WeekType"] == "Weekday"]
    .groupby("Month")["Congestion Level"].mean()
    .reindex(month_order)
)
monthly_we = (
    df[df["WeekType"] == "Weekend"]
    .groupby("Month")["Congestion Level"].mean()
    .reindex(month_order)
)

fig, ax = plt.subplots(figsize=(11, 5))

ax.plot(month_order, monthly.values,    color="#e74c3c", marker="o",
        linewidth=2.2, markersize=7, label="Overall Avg")
ax.plot(month_order, monthly_wd.values, color="#2980b9", marker="s",
        linewidth=1.5, markersize=5, linestyle="--", label="Weekday Avg")
ax.plot(month_order, monthly_we.values, color="#27ae60", marker="^",
        linewidth=1.5, markersize=5, linestyle=":",  label="Weekend Avg")

ax.axhline(city_avg, color="gray", linestyle="--", linewidth=1,
           label=f"City Mean: {city_avg:.1f}")

ax.set_xticks(month_order)
ax.set_xticklabels(month_labels, fontsize=10)
ax.set_ylabel("Mean Congestion Level (0–100)", fontsize=11)
ax.set_title("Monthly Congestion Trend — Bangalore (2022–2024)\nWeekday vs Weekend Breakdown",
             fontsize=13, fontweight="bold", pad=12)
ax.legend(fontsize=10)
ax.spines[["top", "right"]].set_visible(False)
ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())
plt.tight_layout()

save_path = os.path.join(IMAGES_DIR, "monthly_trend.png")
plt.savefig(save_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved → {save_path}")

print("\n" + "=" * 60)
print("STEP 9 : Congestion Severity Classification")
print("=" * 60)

# Define 4 bands based on the 0-100 Congestion Level scale
def classify_severity(level):
    if level < 50:
        return "Low (<50)"
    elif level < 75:
        return "Moderate (50–75)"
    elif level < 90:
        return "High (75–90)"
    else:
        return "Critical (>90)"

df["Severity"] = df["Congestion Level"].apply(classify_severity)

# Count and percentage per band
severity_count = df["Severity"].value_counts()
severity_pct   = (severity_count / len(df) * 100).round(1)

# Ordered for printing
band_order = ["Critical (>90)", "High (75–90)", "Moderate (50–75)", "Low (<50)"]

print(f"\n  Severity breakdown across {len(df):,} records:")
print("  " + "-" * 40)
for band in band_order:
    count = severity_count.get(band, 0)
    pct   = severity_pct.get(band, 0.0)
    bar   = "█" * int(pct / 2)   # simple ASCII bar
    print(f"  {band:<20} : {count:>5} records  ({pct:.1f}%)  {bar}")
print("  " + "-" * 40)

# Top 5 roads: what % of their records are Critical?
print("\n  Critical-severity record % for Top 5 Chokepoints:")
for road in top5_roads:
    road_df   = df[df["Road/Intersection Name"] == road]
    crit_pct  = (road_df["Severity"] == "Critical (>90)").mean() * 100
    print(f"    {road:<28} : {crit_pct:.1f}% records Critical")

# Traffic volume share of top 5
top5_vol_share = (
    df[df["Road/Intersection Name"].isin(top5_roads)]["Traffic Volume"].sum()
    / df["Traffic Volume"].sum() * 100
)
print(f"\n  Top 5 roads handle {top5_vol_share:.1f}% of total measured traffic volume")

print("\n" + "=" * 60)
print("STEP 10: Weather Impact on Congestion")
print("=" * 60)

# Mean congestion per weather condition
weather_cong = (
    df.groupby("Weather Conditions")["Congestion Level"]
    .mean()
    .sort_values(ascending=False)
)

clear_avg = weather_cong["Clear"]
print(f"\n  Baseline (Clear weather) congestion: {clear_avg:.2f}")
print("\n  Congestion by Weather Condition:")
for weather, val in weather_cong.items():
    diff = val - clear_avg
    sign = "+" if diff >= 0 else ""
    print(f"    {weather:<12} : {val:.2f}  ({sign}{diff:.2f} vs Clear)")

# Count of records per weather type
weather_count = df["Weather Conditions"].value_counts()
print("\n  Record count per weather type:")
for w, c in weather_count.items():
    print(f"    {w:<12} : {c:,} records")

# Plot: weather vs mean congestion (horizontal bar)
fig, ax = plt.subplots(figsize=(9, 4))

weather_sorted = weather_cong.sort_values()  # ascending for horizontal bar
bar_colors = ["#c0392b" if v > clear_avg else "#2ecc71" for v in weather_sorted.values]
bars = ax.barh(weather_sorted.index, weather_sorted.values,
               color=bar_colors, edgecolor="white", height=0.5)

# Baseline reference line
ax.axvline(clear_avg, color="#2c3e50", linestyle="--", linewidth=1.5,
           label=f"Clear baseline: {clear_avg:.1f}")

# Value labels
for bar, val in zip(bars, weather_sorted.values):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}", va="center", fontsize=10, fontweight="bold")

ax.set_xlabel("Mean Congestion Level (0–100)", fontsize=11)
ax.set_title("Impact of Weather Conditions on Congestion Level",
             fontsize=13, fontweight="bold", pad=12)
ax.legend(fontsize=10)
ax.set_xlim(78, 84)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()

save_path = os.path.join(IMAGES_DIR, "weather_impact.png")
plt.savefig(save_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"\n  Saved → {save_path}")

#  FINAL SUMMARY PRINTOUT
print("\n" + "=" * 60)
print("ANALYSIS COMPLETE — KEY FINDINGS")
print("=" * 60)
print(f"  Total records analysed         : {len(df):,}")
print(f"  Date range                     : {df['Date'].min().date()} to {df['Date'].max().date()}")
print(f"  Roads / Areas covered          : {df['Road/Intersection Name'].nunique()} roads, {df['Area Name'].nunique()} areas")
print(f"  City-wide avg congestion       : {city_avg:.2f} / 100")
print(f"  Top-5 avg congestion           : {top5_avg:.2f} / 100  (+{pct_diff:.1f}% above city avg)")
print(f"  Most congested road            : {top5.idxmax()}")
crit_total_pct = severity_pct.get("Critical (>90)", 0)
print(f"  Critical congestion records    : {crit_total_pct:.1f}% of all observations")
print(f"  Top-5 roads traffic share      : {top5_vol_share:.1f}% of total volume")
print(f"  Windiest weather congestion    : {weather_cong['Windy']:.2f} (+{weather_cong['Windy']-clear_avg:.2f} vs Clear)")
print(f"  Estimated daily economic loss  : Rs {grand_total:,.0f}  (Rs {grand_total/100000:.1f} lakh)")
print(f"  Plots saved to                 : {IMAGES_DIR}")
print("=" * 60)
