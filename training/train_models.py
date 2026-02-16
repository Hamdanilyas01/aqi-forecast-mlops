import os
import pandas as pd
import joblib
from pymongo import MongoClient
from dotenv import load_dotenv

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

# -----------------------------
# Load Environment
# -----------------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["aqi_project"]
collection = db["features"]

# -----------------------------
# Load Data
# -----------------------------
df = pd.DataFrame(list(collection.find()))
df.drop(columns=["_id"], inplace=True)

# Sort for time-series integrity
df = df.sort_values("timestamp")

# -----------------------------
# Feature Selection
# -----------------------------
feature_columns = [
    # Current values
    "pm2_5",
    "pm10",

    # Weather
    "temperature",
    "humidity",
    "wind_speed",
    "pressure",

    # Time
    "hour",
    "day_of_week",

    # Lags
    "pm2_5_lag1",
    "pm2_5_lag3",
    "pm2_5_lag6",
    "pm2_5_lag12",
    "pm2_5_lag24",

    # Rolling means
    "pm2_5_roll_mean_3",
    "pm2_5_roll_mean_6",
    "pm2_5_roll_mean_12",
    "pm2_5_roll_mean_24",

    # Volatility
    "pm2_5_roll_std_3",
    "pm2_5_roll_std_6",
]

target_column = "target_pm2_5"

X = df[feature_columns]
y = df[target_column]

# -----------------------------
# Train/Test Split (NO SHUFFLE)
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    shuffle=False
)

# -----------------------------
# Define Models
# -----------------------------
models = {
    "RandomForest": RandomForestRegressor(
        n_estimators=400,
        max_depth=15,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    ),

    "Ridge": Ridge(),

    "GradientBoosting": GradientBoostingRegressor(
        n_estimators=500,
        learning_rate=0.03,
        max_depth=4,
        min_samples_split=5,
        min_samples_leaf=2,
        subsample=0.8,
        random_state=42
    )
}

results = {}
best_model_name = None
best_rmse = float("inf")

# -----------------------------
# Train & Evaluate
# -----------------------------
for name, model in models.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    rmse = np.sqrt(mean_squared_error(y_test, preds))
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    results[name] = {
        "RMSE": rmse,
        "MAE": mae,
        "R2": r2
    }

    print(f"\nModel: {name}")
    print("RMSE:", rmse)
    print("MAE:", mae)
    print("R2:", r2)

    # Save model
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_DIR = os.path.join(BASE_DIR, "models")
    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(model, os.path.join(MODEL_DIR, f"{name}.pkl"))

    # Track best model
    if rmse < best_rmse:
        best_rmse = rmse
        best_model_name = name

print("\n✅ Best Model:", best_model_name)

# -----------------------------
# Save Metrics to MongoDB
# -----------------------------
metrics_collection = db["model_metrics"]

metrics_collection.insert_one({
    "results": results,
    "best_model": best_model_name
})

print("✅ Training pipeline completed successfully")
