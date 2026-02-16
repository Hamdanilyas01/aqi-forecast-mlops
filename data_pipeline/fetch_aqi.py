import requests
import os
from dotenv import load_dotenv

load_dotenv()

AQICN_TOKEN = os.getenv("AQICN_TOKEN")

def fetch_aqi(city="Lahore"):
    url = f"https://api.waqi.info/feed/{city}/?token={AQICN_TOKEN}"
    response = requests.get(url).json()

    if response["status"] != "ok":
        raise Exception(f"AQICN API error: {response}")

    data = response["data"]
    iaqi = data.get("iaqi", {})

    return {
        "city": city,
        "timestamp": data["time"]["s"],
        "aqi": int(data["aqi"]),
        "pm25": float(iaqi.get("pm25", {}).get("v", 0.0)),
        "pm10": float(iaqi.get("pm10", {}).get("v", 0.0)),
        "no2": float(iaqi.get("no2", {}).get("v", 0.0)),
        "so2": float(iaqi.get("so2", {}).get("v", 0.0)),
    }
