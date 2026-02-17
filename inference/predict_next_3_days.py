import os
import pandas as pd
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import timedelta

from inference.load_best_model import load_production_model

# -----------------------------
# Load Environment
# -----------------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client["aqi_project"]
features_collection = db["features"]
hourly_collection = db["forecast_hourly"]
daily_collection = db["forecast_daily"]

# Clear previous forecasts
hourly_collection.delete_many({})
daily_collection.delete_many({})

# -----------------------------
# Load Latest Features
# -----------------------------
df = pd.DataFrame(list(features_collection.find()))
df.drop(columns=["_id"], inplace=True)
df = df.sort_values("timestamp")

last_row = df.iloc[-1:].copy()

# -----------------------------
# Load Production Model
# -----------------------------
model, feature_columns = load_production_model()

# -----------------------------
# AQI Conversion
# -----------------------------
def pm25_to_aqi(pm25):
    breakpoints = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
    ]

    for pm_low, pm_high, aqi_low, aqi_high in breakpoints:
        if pm_low <= pm25 <= pm_high:
            return ((aqi_high - aqi_low) / (pm_high - pm_low)) * (pm25 - pm_low) + aqi_low

    return 300


def aqi_category(aqi):
    if aqi <= 50:
        return "Good", "#00E400"
    elif aqi <= 100:
        return "Moderate", "#FFFF00"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "#FF7E00"
    elif aqi <= 200:
        return "Unhealthy", "#FF0000"
    else:
        return "Very Unhealthy", "#8F3F97"


# -----------------------------
# Generate 72 Hour Forecast
# -----------------------------
forecast_rows = []
current_row = last_row.copy()

for _ in range(72):

    # Ensure correct feature order from registry
    X_input = current_row[feature_columns]

    predicted_pm25 = model.predict(X_input)[0]

    # Update lag chain
    if "pm2_5_lag24" in current_row.columns:
        current_row["pm2_5_lag24"] = current_row.get("pm2_5_lag12", current_row["pm2_5_lag24"])

    if "pm2_5_lag12" in current_row.columns:
        current_row["pm2_5_lag12"] = current_row.get("pm2_5_lag6", current_row["pm2_5_lag12"])

    if "pm2_5_lag6" in current_row.columns:
        current_row["pm2_5_lag6"] = current_row.get("pm2_5_lag3", current_row["pm2_5_lag6"])

    if "pm2_5_lag3" in current_row.columns:
        current_row["pm2_5_lag3"] = current_row.get("pm2_5_lag1", current_row["pm2_5_lag3"])

    if "pm2_5_lag1" in current_row.columns:
        current_row["pm2_5_lag1"] = predicted_pm25

    current_row["pm2_5"] = predicted_pm25

    # Update timestamp
    current_row["timestamp"] = pd.to_datetime(current_row["timestamp"]) + timedelta(hours=1)

    # Update time features safely
    if "hour" in current_row.columns:
        current_row["hour"] = current_row["timestamp"].dt.hour

    if "day_of_week" in current_row.columns:
        current_row["day_of_week"] = current_row["timestamp"].dt.dayofweek

    # Convert to AQI
    predicted_aqi = pm25_to_aqi(predicted_pm25)
    category, color = aqi_category(predicted_aqi)

    forecast_rows.append({
        "timestamp": current_row["timestamp"].iloc[0],
        "predicted_pm2_5": float(predicted_pm25),
        "predicted_aqi": round(predicted_aqi, 2),
        "category": category,
        "color": color
    })

# Convert to DataFrame
forecast_df = pd.DataFrame(forecast_rows)

# Store hourly forecast
hourly_collection.insert_many(forecast_df.to_dict("records"))

print("✅ 72-hour forecast stored")

# -----------------------------
# DAILY AGGREGATION
# -----------------------------
forecast_df["date"] = forecast_df["timestamp"].dt.strftime("%Y-%m-%d")

daily_df = forecast_df.groupby("date").agg({
    "predicted_pm2_5": "mean",
    "predicted_aqi": ["mean", "max", "min"]
}).reset_index()

daily_df.columns = [
    "date",
    "avg_pm2_5",
    "avg_aqi",
    "max_aqi",
    "min_aqi"
]

daily_rows = []

for _, row in daily_df.iterrows():
    category, color = aqi_category(row["avg_aqi"])

    daily_rows.append({
        "date": row["date"],
        "avg_pm2_5": float(row["avg_pm2_5"]),
        "avg_aqi": round(row["avg_aqi"], 2),
        "max_aqi": round(row["max_aqi"], 2),
        "min_aqi": round(row["min_aqi"], 2),
        "category": category,
        "color": color
    })

daily_collection.insert_many(daily_rows)

print("✅ Daily summary stored")
print("Total hourly rows:", len(forecast_df))
print("Total daily rows:", len(daily_rows))
