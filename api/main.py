import os
from fastapi import FastAPI
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# -----------------------------
# Load Environment
# -----------------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["aqi_project"]

hourly_collection = db["forecast_hourly"]
daily_collection = db["forecast_daily"]

app = FastAPI(title="AQI Forecast API")


# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
def root():
    return {"message": "AQI Forecast API is running"}


# -----------------------------
# Hourly Forecast (72 rows)
# -----------------------------
@app.get("/forecast/hourly")
def get_hourly_forecast():
    data = list(hourly_collection.find({}, {"_id": 0}))
    return {
        "count": len(data),
        "data": data
    }


# -----------------------------
# Daily Forecast (3 rows)
# -----------------------------
@app.get("/forecast/daily")
def get_daily_forecast():
    data = list(daily_collection.find({}, {"_id": 0}))
    return {
        "count": len(data),
        "data": data
    }


# -----------------------------
# Latest AQI (Next Hour)
# -----------------------------
@app.get("/forecast/latest")
def get_latest():
    doc = hourly_collection.find_one(
        sort=[("timestamp", 1)],
        projection={"_id": 0}
    )

    return doc
