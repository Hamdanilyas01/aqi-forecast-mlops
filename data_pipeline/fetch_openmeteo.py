import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta

LAT = 24.8607
LON = 67.0011


def fetch_openmeteo_data():
    # -----------------------------
    # Date range (last 90 days)
    # -----------------------------
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=90)

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # -----------------------------
    # Setup Open-Meteo client
    # -----------------------------
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # -----------------------------
    # AIR QUALITY API
    # -----------------------------
    air_quality_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    air_params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": ["pm2_5", "pm10"],
        "start_date": start_date_str,
        "end_date": end_date_str,
    }

    air_response = openmeteo.weather_api(air_quality_url, params=air_params)[0]
    air_hourly = air_response.Hourly()

    air_df = pd.DataFrame({
        "timestamp": pd.date_range(
            start=pd.to_datetime(air_hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(air_hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=air_hourly.Interval()),
            inclusive="left"
        ),
        "pm2_5": air_hourly.Variables(0).ValuesAsNumpy(),
        "pm10": air_hourly.Variables(1).ValuesAsNumpy(),
    })

    # -----------------------------
    # WEATHER API
    # -----------------------------
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "surface_pressure"
        ],
        "start_date": start_date_str,
        "end_date": end_date_str,
    }

    weather_response = openmeteo.weather_api(weather_url, params=weather_params)[0]
    weather_hourly = weather_response.Hourly()

    weather_df = pd.DataFrame({
        "timestamp": pd.date_range(
            start=pd.to_datetime(weather_hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(weather_hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=weather_hourly.Interval()),
            inclusive="left"
        ),
        "temperature": weather_hourly.Variables(0).ValuesAsNumpy(),
        "humidity": weather_hourly.Variables(1).ValuesAsNumpy(),
        "wind_speed": weather_hourly.Variables(2).ValuesAsNumpy(),
        "wind_direction": weather_hourly.Variables(3).ValuesAsNumpy(),
        "pressure": weather_hourly.Variables(4).ValuesAsNumpy(),
    })

    # -----------------------------
    # Merge Air + Weather
    # -----------------------------
    df = pd.merge(air_df, weather_df, on="timestamp", how="inner")

    return df


if __name__ == "__main__":
    df = fetch_openmeteo_data()
    print(df.head())
    print("Rows:", len(df))
