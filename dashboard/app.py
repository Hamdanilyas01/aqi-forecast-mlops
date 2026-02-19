

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pymongo import MongoClient
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="AQI Forecast Dashboard", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #0E1117;
}

/* 🔥 GLOBAL TEXT FIX */
h1, h2, h3, h4, h5, h6 {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Section titles */
.css-10trblm, .css-18e3th9 {
    color: #FFFFFF !important;
}

/* Health box brighter */
div[data-testid="stAlert"] {
    background-color: #132235 !important;
    color: #FFFFFF !important;
}

/* 3-day card text */
.card-text {
    color: #FFFFFF !important;
}

/* Weather styling */
.weather-label {
    color: #CFCFCF !important;
    font-size: 14px;
}

.weather-value {
    color: #FFFFFF !important;
    font-size: 26px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st_autorefresh(interval=3600 * 1000, key="hourly_refresh")

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------
MONGO_URI = st.secrets["MONGO_URI"]

client = MongoClient(MONGO_URI)
db = client["aqi_project"]

hourly_collection = db["forecast_hourly"]
daily_collection = db["forecast_daily"]
registry_collection = db["model_registry"]
features_collection = db["features"]
shap_collection = db["model_shap"]

# --------------------------------------------------
# FETCH DATA
# --------------------------------------------------
hourly = list(hourly_collection.find({}, {"_id": 0}))
daily = list(daily_collection.find({}, {"_id": 0}))
model_info = registry_collection.find_one({"is_production": True})
current_weather = features_collection.find_one(sort=[("timestamp", -1)])
shap_data = list(shap_collection.find({}, {"_id": 0}))

hourly_df = pd.DataFrame(hourly)
daily_df = pd.DataFrame(daily)
shap_df = pd.DataFrame(shap_data)

if not hourly_df.empty:
    hourly_df["timestamp"] = pd.to_datetime(hourly_df["timestamp"])

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("Karachi Air Quality Forecast")
st.markdown("---")

# --------------------------------------------------
# CURRENT AQI
# --------------------------------------------------
if not hourly_df.empty:
    latest = hourly_df.iloc[0]
    col1, col2 = st.columns([1, 1])

    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest["predicted_aqi"],
            title={'text': "Current AQI"},
            gauge={
                'axis': {'range': [0, 300]},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [0, 50], 'color': "#00e400"},
                    {'range': [50, 100], 'color': "#ffff00"},
                    {'range': [100, 150], 'color': "#ff7e00"},
                    {'range': [150, 200], 'color': "#ff0000"},
                    {'range': [200, 300], 'color': "#8f3f97"},
                ],
            }
        ))

        fig.update_layout(
            height=350,
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            font=dict(color="white")
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("PM2.5 (µg/m³)")
        st.markdown(f"## {round(latest['predicted_pm2_5'], 2)}")
        st.markdown(f"**Status:** {latest['category']}")

    st.markdown("---")

    def recommendation(category):
        if category == "Good":
            return "Air quality is good. Enjoy outdoor activities."
        elif category == "Moderate":
            return "Air quality is moderate. Sensitive individuals should limit prolonged outdoor exertion."
        elif category == "Unhealthy for Sensitive Groups":
            return "Sensitive groups should reduce prolonged outdoor activity."
        elif category == "Unhealthy":
            return "Everyone should limit outdoor activity."
        else:
            return "Avoid outdoor exposure. Stay indoors if possible."

    st.info(f"Health Recommendation: {recommendation(latest['category'])}")

# --------------------------------------------------
# LINE CHART
# --------------------------------------------------
st.markdown("---")
st.subheader("72-Hour Forecast")

if not hourly_df.empty:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hourly_df["timestamp"],
        y=hourly_df["predicted_pm2_5"],
        mode="lines",
        name="PM2.5",
        line=dict(color="#1f77b4", dash="dot")
    ))

    fig.add_trace(go.Scatter(
        x=hourly_df["timestamp"],
        y=hourly_df["predicted_aqi"],
        mode="lines",
        name="AQI",
        line=dict(color="#ff7f0e", dash="dot")
    ))

    fig.update_layout(
        height=450,
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font=dict(color="white"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )

    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# 3 DAY SUMMARY
# --------------------------------------------------
st.markdown("---")
st.subheader("3-Day Summary")

if not daily_df.empty:
    cols = st.columns(len(daily_df))

    for i, (_, row) in enumerate(daily_df.iterrows()):
        with cols[i]:
            st.markdown(f"""
                <div style="background-color:#1c1f26;
                            padding:18px;
                            border-radius:12px;
                            text-align:center;">
                    <h4>{row['date']}</h4>
                    <p class="card-text"><b>Avg AQI:</b> {round(row['avg_aqi'],2)}</p>
                    <p class="card-text"><b>Max:</b> {round(row['max_aqi'],2)}</p>
                    <p class="card-text"><b>Min:</b> {round(row['min_aqi'],2)}</p>
                    <p class="card-text">{row['category']}</p>
                </div>
            """, unsafe_allow_html=True)

# --------------------------------------------------
# CURRENT WEATHER
# --------------------------------------------------
st.markdown("---")
st.subheader("Current Weather")

if current_weather:
    w1, w2, w3, w4 = st.columns(4)

    w1.markdown(f"<div class='weather-label'>Temperature (°C)</div><div class='weather-value'>{round(current_weather.get('temperature', 0), 2)}</div>", unsafe_allow_html=True)
    w2.markdown(f"<div class='weather-label'>Humidity (%)</div><div class='weather-value'>{round(current_weather.get('humidity', 0), 2)}</div>", unsafe_allow_html=True)
    w3.markdown(f"<div class='weather-label'>Wind Speed (km/h)</div><div class='weather-value'>{round(current_weather.get('wind_speed', 0), 2)}</div>", unsafe_allow_html=True)
    w4.markdown(f"<div class='weather-label'>Pressure (hPa)</div><div class='weather-value'>{round(current_weather.get('pressure', 0), 2)}</div>", unsafe_allow_html=True)

# --------------------------------------------------
# MODEL INFO
# --------------------------------------------------
st.markdown("---")
st.subheader("Production Model")

if model_info:
    st.markdown(f"""
        <div style="background-color:#1c1f26;
                    padding:20px;
                    border-radius:12px;">
            <h4>{model_info['model_name']}</h4>
            <p class="card-text"><b>RMSE:</b> {round(model_info['metrics']['RMSE'],3)}</p>
            <p class="card-text"><b>MAE:</b> {round(model_info['metrics']['MAE'],3)}</p>
            <p class="card-text"><b>R²:</b> {round(model_info['metrics']['R2'],3)}</p>
        </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# SHAP FEATURE IMPORTANCE
# --------------------------------------------------
st.markdown("---")
st.subheader("Feature Importance (SHAP)")

if not shap_df.empty:
    shap_df = shap_df.sort_values("importance", ascending=False)

    fig = go.Figure(go.Bar(
        x=shap_df["importance"],
        y=shap_df["feature"],
        orientation="h",
        marker_color="#1f77b4"
    ))

    fig.update_layout(
        height=500,
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font=dict(color="white")
    )

    st.plotly_chart(fig, use_container_width=True)
