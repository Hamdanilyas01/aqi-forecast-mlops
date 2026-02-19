🌍 Karachi AQI Forecasting – End-to-End MLOps System
📌 Project Overview

This project implements a fully automated end-to-end MLOps pipeline for forecasting Air Quality Index (AQI) in Karachi.

The system:

Ingests live weather & pollution data

Engineers time-series features

Trains and evaluates multiple ML models

Maintains a model registry with versioning

Automatically retrains models daily

Generates 72-hour recursive forecasts

Provides SHAP-based explainability

Deploys a live interactive dashboard

This project demonstrates real-world production ML engineering, not just model training.


🚀 Live Deployment
🔗 Dashboard: (https://aqi-forecast-mlops-ali-hamdan.streamlit.app/)


🔁 Automation (CI/CD)
Feature Pipeline

Runs every hour

Pulls latest weather + pollution data

Engineers lag & rolling features

Stores in MongoDB

Training Pipeline

Runs daily

Trains 3 models

Selects best model by RMSE

Registers new model version

Updates production model

Computes SHAP feature importance

🤖 Models Evaluated

RandomForest

Ridge Regression

GradientBoosting (Selected Production Model)

Best performance:

RMSE ≈ 3.97

MAE ≈ 2.51

R² ≈ 0.90+

📦 Model Registry (Custom Built)

Each model version stores:

Model name

Version number

Metrics

Feature list

Model path

Production flag

Timestamp

Only one model is marked as is_production=True.




🔮 Forecasting

Recursive 72-hour prediction

Converts PM2.5 → AQI

Stores hourly & daily aggregates

Health recommendations based on AQI category

📊 SHAP Explainability

SHAP is used to:

Measure feature importance

Validate lag feature contribution

Show interpretability on dashboard

🖥 Dashboard Features

AQI Gauge

Current PM2.5

Health Recommendation

72-hour forecast (PM2.5 + AQI)

3-day summary cards

Current weather metrics

Production model metrics

SHAP feature importance

Auto-refresh hourly

🛠 Tech Stack

Python 3.11

MongoDB

Scikit-learn

SHAP

GitHub Actions

Streamlit

Plotly



⚠ Challenges Faced
Hopsworks Integration Failure

Identity verification restrictions

Limited free-tier features

CI/CD integration complexity

Resolution:

Implemented custom MongoDB-based feature store & model registry.
