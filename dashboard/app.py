import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import time

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="AQI Forecast Dashboard", layout="wide")

# Dark Premium Styling + Smooth Animations
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    div[data-testid="stMetric"],
    div[data-testid="stMarkdownContainer"],
    .stPlotlyChart {
        transition: all 0.4s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: scale(1.03);
    }
</style>
""", unsafe_allow_html=True)

# Auto refresh every hour
st_autorefresh(interval=3600 * 1000, key="hourly_refresh")

API_URL = "http://127.0.0.1:8000"

# --------------------------------------------------
# FETCH DATA
# --------------------------------------------------
hourly = requests.get(f"{API_URL}/forecast/hourly").json()
daily = requests.get(f"{API_URL}/forecast/daily").json()
model_info = requests.get(f"{API_URL}/model/info").json()
current_weather = requests.get(f"{API_URL}/weather/current").json()

hourly_df = pd.DataFrame(hourly)
daily_df = pd.DataFrame(daily)

if not hourly_df.empty:
    hourly_df["timestamp"] = pd.to_datetime(hourly_df["timestamp"])

latest = hourly_df.iloc[0]

# --------------------------------------------------
# AQI GLOW COLOR LOGIC
# --------------------------------------------------
def get_glow_color(aqi):
    if aqi <= 50:
        return "0 0 30px #00E400"
    elif aqi <= 100:
        return "0 0 30px #FFFF00"
    elif aqi <= 150:
        return "0 0 30px #FF7E00"
    elif aqi <= 200:
        return "0 0 30px #FF0000"
    else:
        return "0 0 30px #8F3F97"

glow = get_glow_color(latest["predicted_aqi"])

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("Karachi Air Quality Forecast")
st.markdown("---")

# --------------------------------------------------
# CURRENT AQI + PM2.5
# --------------------------------------------------
col1, col2 = st.columns([1,1])

# Animated Gauge
with col1:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(latest["predicted_aqi"], 2),
        title={'text': "Current AQI"},
        gauge={
            'axis': {'range': [0, 300]},
            'bar': {'color': "#0A3D62"},
            'steps': [
                {'range': [0, 50], 'color': "#1b5e20"},
                {'range': [50, 100], 'color': "#827717"},
                {'range': [100, 150], 'color': "#e65100"},
                {'range': [150, 200], 'color': "#b71c1c"},
            ],
        }
    ))
    fig.update_layout(height=350, paper_bgcolor="#0E1117", font_color="white")
    st.plotly_chart(fig, use_container_width=True)

# Animated PM2.5 Card with Glow
with col2:
    pm25_placeholder = st.empty()

    for i in range(0, int(latest['predicted_pm2_5']) + 1, 2):
        pm25_placeholder.markdown(f"""
            <div style="
                background-color:#1E1E1E;
                padding:25px;
                border-radius:12px;
                text-align:center;
                box-shadow:{glow};
                transition: all 0.4s ease-in-out;">
                <h4 style="color:#AAAAAA;">Current PM2.5</h4>
                <h2 style="color:#4FC3F7;">
                    {round(i,2)} µg/m³
                </h2>
                <p style="color:#CCCCCC;">
                    Category: {latest['category']}
                </p>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(0.02)

st.markdown("---")

# --------------------------------------------------
# HEALTH RECOMMENDATION
# --------------------------------------------------
def health_recommendation(aqi):
    if aqi <= 50:
        return "Air quality is good. Perfect for outdoor activities."
    elif aqi <= 100:
        return "Moderate air quality. Sensitive individuals should limit prolonged outdoor exposure."
    elif aqi <= 150:
        return "Unhealthy for sensitive groups. Reduce outdoor activity."
    elif aqi <= 200:
        return "Unhealthy. Avoid prolonged outdoor exposure."
    else:
        return "Very unhealthy. Stay indoors."

st.markdown("### Health Recommendation")
st.info(health_recommendation(latest["predicted_aqi"]))

st.markdown("---")

# --------------------------------------------------
# 72 HOUR FORECAST CHART
# --------------------------------------------------
st.subheader("72-Hour Forecast")

fig = go.Figure()

# PM2.5
fig.add_trace(go.Scatter(
    x=hourly_df["timestamp"],
    y=hourly_df["predicted_pm2_5"].round(2),
    mode="lines",
    name="PM2.5",
    line=dict(color="#0A3D62", dash="dot"),
    fill="tozeroy",
    fillcolor="rgba(10,61,98,0.15)",
))

# AQI
fig.add_trace(go.Scatter(
    x=hourly_df["timestamp"],
    y=hourly_df["predicted_aqi"].round(2),
    mode="lines",
    name="Predicted AQI",
    line=dict(color="#4FC3F7", dash="dot"),
))

fig.update_layout(
    xaxis_title="Date & Time",
    yaxis_title="Value",
    height=450,
    plot_bgcolor="#0E1117",
    paper_bgcolor="#0E1117",
    font_color="white"
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --------------------------------------------------
# WEATHER SECTION
# --------------------------------------------------
st.subheader("Current Weather Conditions")

w1, w2, w3, w4 = st.columns(4)

w1.metric("Temperature (°C)", round(current_weather.get("temperature", 0), 2))
w2.metric("Humidity (%)", round(current_weather.get("humidity", 0), 2))
w3.metric("Wind Speed (km/h)", round(current_weather.get("wind_speed", 0), 2))
w4.metric("Pressure (hPa)", round(current_weather.get("pressure", 0), 2))

st.markdown("---")

# --------------------------------------------------
# MODEL INFO
# --------------------------------------------------
st.subheader("Model Information")

st.markdown(f"""
    <div style="
        background-color:#1E1E1E;
        padding:20px;
        border-radius:12px;">
        <h4 style="color:#4FC3F7;">Production Model: {model_info['model_name']}</h4>
        <p><b>RMSE:</b> {round(model_info['metrics']['RMSE'],3)}</p>
        <p><b>MAE:</b> {round(model_info['metrics']['MAE'],3)}</p>
        <p><b>R²:</b> {round(model_info['metrics']['R2'],3)}</p>
    </div>
""", unsafe_allow_html=True)

#shap
st.markdown("---")
st.subheader("Model Feature Importance (SHAP)")

shap_data = requests.get(f"{API_URL}/model/shap").json()
shap_df = pd.DataFrame(shap_data)

if not shap_df.empty:
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=shap_df["importance"],
        y=shap_df["feature"],
        orientation="h",
        marker=dict(color="#4FC3F7")
    ))

    fig.update_layout(
        height=500,
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        font_color="white"
    )

    st.plotly_chart(fig, use_container_width=True)
