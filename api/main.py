from fastapi import FastAPI
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# ---------------------------------------------------------
# LOAD ENV
# ---------------------------------------------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI environment variable not set.")

client = MongoClient(MONGO_URI)
db = client["aqi_project"]

hourly_collection = db["forecast_hourly"]
daily_collection = db["forecast_daily"]
registry_collection = db["model_registry"]
features_collection = db["features"]

app = FastAPI(title="AQI Forecast API")


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"message": "AQI Forecast API is running"}


# ---------------------------------------------------------
# HOURLY FORECAST
# ---------------------------------------------------------
@app.get("/forecast/hourly")
def get_hourly_forecast():
    data = list(hourly_collection.find({}, {"_id": 0}))
    return data


# ---------------------------------------------------------
# DAILY FORECAST
# ---------------------------------------------------------
@app.get("/forecast/daily")
def get_daily_forecast():
    data = list(daily_collection.find({}, {"_id": 0}))
    return data


# ---------------------------------------------------------
# LATEST FORECAST
# ---------------------------------------------------------
@app.get("/forecast/latest")
def get_latest_forecast():
    latest = hourly_collection.find_one(
        sort=[("timestamp", -1)],
        projection={"_id": 0}
    )
    return latest


# ---------------------------------------------------------
# CURRENT WEATHER
# ---------------------------------------------------------
@app.get("/weather/current")
def get_current_weather():
    latest = features_collection.find_one(
        sort=[("timestamp", -1)]
    )

    if not latest:
        return {
            "temperature": 0,
            "humidity": 0,
            "wind_speed": 0,
            "pressure": 0
        }

    return {
        "temperature": latest.get("temperature") or 0,
        "humidity": latest.get("humidity") or 0,
        "wind_speed": latest.get("wind_speed") or 0,
        "pressure": latest.get("pressure") or 0
    }


# ---------------------------------------------------------
# SHAP FEATURE IMPORTANCE
# ---------------------------------------------------------
@app.get("/model/shap")
def get_shap():
    shap_data = list(db["model_shap"].find({}, {"_id": 0}))
    shap_data = sorted(shap_data, key=lambda x: x["importance"], reverse=True)
    return shap_data


# ---------------------------------------------------------
# MODEL INFO
# ---------------------------------------------------------
@app.get("/model/info")
def get_model_info():
    production_model = registry_collection.find_one(
        {"is_production": True},
        sort=[("version", -1)]
    )

    if not production_model:
        return {"error": "No production model found"}

    return {
        "model_name": production_model["model_name"],
        "metrics": production_model["metrics"],
        "version": production_model["version"]
    }


# ---------------------------------------------------------
# UVICORN ENTRY POINT (FOR RENDER)
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000)
