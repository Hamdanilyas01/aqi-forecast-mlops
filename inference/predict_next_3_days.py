import os
import pandas as pd
import numpy as np
import joblib
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import timedelta

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

# Use latest row as starting point
last_row = df.iloc[-1:].copy()

# -----------------------------
# Load Best Model
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "GradientBoosting.pkl")

model = joblib.load(MODEL_PATH)

# Feature columns MUST match training
feature_columns = [
    "pm2_5",
    "pm10",
    "temperature",
    "humidity",
    "wind_speed",
    "pressure",
    "hour",
    "day_of_week",
    "pm2_5_lag1",
    "pm2_5_lag3",
    "pm2_5_lag6",
    "pm2_5_lag12",
    "pm2_5_lag24",
    "pm2_5_roll_mean_3",
    "pm2_5_roll_mean_6",
    "pm2_5_roll_mean_12",
    "pm2_5_roll_mean_24",
    "pm2_5_roll_std_3",
    "pm2_5_roll_std_6",
]

# -----------------------------
# AQI Conversion Function
# -----------------------------
def pm25_to_aqi(pm25):
    breakpoints = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
    ]

    for bp in breakpoints:
        pm_low, pm_high, aqi_low, aqi_high = bp
        if pm_low <= pm25 <= pm_high:
            return ((aqi_high - aqi_low) / (pm_high - pm_low)) * (pm25 - pm_low) + aqi_low

    return None


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

for i in range(72):

    X_input = current_row[feature_columns]
    predicted_pm25 = model.predict(X_input)[0]

    # Update lag features manually
    current_row["pm2_5_lag24"] = current_row["pm2_5_lag12"]
    current_row["pm2_5_lag12"] = current_row["pm2_5_lag6"]
    current_row["pm2_5_lag6"] = current_row["pm2_5_lag3"]
    current_row["pm2_5_lag3"] = current_row["pm2_5_lag1"]
    current_row["pm2_5_lag1"] = predicted_pm25

    current_row["pm2_5"] = predicted_pm25

    # Update timestamp
    current_row["timestamp"] = pd.to_datetime(current_row["timestamp"]) + timedelta(hours=1)

    # Update time features
    current_row["hour"] = current_row["timestamp"].dt.hour
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
