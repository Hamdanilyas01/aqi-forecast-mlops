# import os
# import pandas as pd
# import joblib
# import numpy as np
# from datetime import datetime, timezone
# from pymongo import MongoClient
# from dotenv import load_dotenv

# from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
# from sklearn.linear_model import Ridge
# from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


# # =========================================================
# # Load Environment
# # =========================================================
# load_dotenv()

# MONGO_URI = os.getenv("MONGO_URI")
# client = MongoClient(MONGO_URI)
# db = client["aqi_project"]

# features_collection = db["features"]
# metrics_collection = db["model_metrics"]
# registry_collection = db["model_registry"]


# # =========================================================
# # Load Data
# # =========================================================
# df = pd.DataFrame(list(features_collection.find()))
# df.drop(columns=["_id"], inplace=True)

# df = df.sort_values("timestamp")


# # =========================================================
# # Feature Selection
# # =========================================================
# feature_columns = [
#     "pm2_5",
#     "pm10",
#     "temperature",
#     "humidity",
#     "wind_speed",
#     "pressure",
#     "hour",
#     "day_of_week",
#     "pm2_5_lag1",
#     "pm2_5_lag3",
#     "pm2_5_lag6",
#     "pm2_5_lag12",
#     "pm2_5_lag24",
#     "pm2_5_roll_mean_3",
#     "pm2_5_roll_mean_6",
#     "pm2_5_roll_mean_12",
#     "pm2_5_roll_mean_24",
#     "pm2_5_roll_std_3",
#     "pm2_5_roll_std_6",
# ]

# target_column = "target_pm2_5"

# X = df[feature_columns]
# y = df[target_column]


# # =========================================================
# # Train/Test Split
# # =========================================================
# X_train, X_test, y_train, y_test = train_test_split(
#     X,
#     y,
#     test_size=0.2,
#     shuffle=False
# )


# # =========================================================
# # Define Models
# # =========================================================
# models = {
#     "RandomForest": RandomForestRegressor(
#         n_estimators=400,
#         max_depth=15,
#         min_samples_split=4,
#         min_samples_leaf=2,
#         random_state=42,
#         n_jobs=-1
#     ),

#     "Ridge": Ridge(),

#     "GradientBoosting": GradientBoostingRegressor(
#         n_estimators=500,
#         learning_rate=0.03,
#         max_depth=4,
#         min_samples_split=5,
#         min_samples_leaf=2,
#         subsample=0.8,
#         random_state=42
#     )
# }


# results = {}
# best_model_name = None
# best_model_object = None
# best_rmse = float("inf")


# # =========================================================
# # Train & Evaluate
# # =========================================================
# for name, model in models.items():

#     model.fit(X_train, y_train)
#     preds = model.predict(X_test)

#     rmse = np.sqrt(mean_squared_error(y_test, preds))
#     mae = mean_absolute_error(y_test, preds)
#     r2 = r2_score(y_test, preds)

#     results[name] = {
#         "RMSE": float(rmse),
#         "MAE": float(mae),
#         "R2": float(r2)
#     }

#     print(f"\nModel: {name}")
#     print("RMSE:", rmse)
#     print("MAE:", mae)
#     print("R2:", r2)

#     # Save model locally
#     BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     MODEL_DIR = os.path.join(BASE_DIR, "models")
#     os.makedirs(MODEL_DIR, exist_ok=True)

#     model_path = os.path.join(MODEL_DIR, f"{name}.pkl")
#     joblib.dump(model, model_path)

#     # Track best model
#     if rmse < best_rmse:
#         best_rmse = rmse
#         best_model_name = name
#         best_model_object = model


# print("\n✅ Best Model:", best_model_name)


# # =========================================================
# # Save Metrics Snapshot
# # =========================================================
# metrics_collection.insert_one({
#     "timestamp": datetime.now(timezone.utc),
#     "results": results,
#     "best_model": best_model_name
# })


# # =========================================================
# # MODEL REGISTRY
# # =========================================================

# # 1️⃣ Determine next version
# latest_model = registry_collection.find_one(
#     sort=[("version", -1)]
# )

# next_version = 1
# if latest_model:
#     next_version = latest_model["version"] + 1


# # 2️⃣ Set all existing models to NOT production
# registry_collection.update_many(
#     {},
#     {"$set": {"is_production": False}}
# )


# # 3️⃣ Register new production model
# registry_collection.insert_one({
#     "model_name": best_model_name,
#     "version": next_version,
#     "metrics": results[best_model_name],
#     "feature_columns": feature_columns,
#     "model_path": f"models/{best_model_name}.pkl",
#     "is_production": True,
#     "created_at": datetime.now(timezone.utc)
# })

# print(f"✅ Model Registry Updated — Version {next_version} is now PRODUCTION")
# print("✅ Training pipeline completed successfully")



import os
import pandas as pd
import joblib
import numpy as np
import shap
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# =========================================================
# Load Environment
# =========================================================
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["aqi_project"]

features_collection = db["features"]
metrics_collection = db["model_metrics"]
registry_collection = db["model_registry"]
shap_collection = db["model_shap"]

# =========================================================
# Load Data
# =========================================================
df = pd.DataFrame(list(features_collection.find()))
df.drop(columns=["_id"], inplace=True)
df = df.sort_values("timestamp")

# =========================================================
# Feature Selection
# =========================================================
feature_columns = [
    "pm2_5", "pm10",
    "temperature", "humidity", "wind_speed", "pressure",
    "hour", "day_of_week",
    "pm2_5_lag1", "pm2_5_lag3", "pm2_5_lag6",
    "pm2_5_lag12", "pm2_5_lag24",
    "pm2_5_roll_mean_3", "pm2_5_roll_mean_6",
    "pm2_5_roll_mean_12", "pm2_5_roll_mean_24",
    "pm2_5_roll_std_3", "pm2_5_roll_std_6",
]

target_column = "target_pm2_5"

X = df[feature_columns]
y = df[target_column]

# =========================================================
# Train/Test Split
# =========================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    shuffle=False
)

# =========================================================
# Define Models
# =========================================================
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
best_model_object = None
best_rmse = float("inf")

# =========================================================
# Train & Evaluate
# =========================================================
for name, model in models.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    rmse = np.sqrt(mean_squared_error(y_test, preds))
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    results[name] = {
        "RMSE": float(rmse),
        "MAE": float(mae),
        "R2": float(r2)
    }

    print(f"\nModel: {name}")
    print("RMSE:", rmse)
    print("MAE:", mae)
    print("R2:", r2)

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_DIR = os.path.join(BASE_DIR, "models")
    os.makedirs(MODEL_DIR, exist_ok=True)

    model_path = os.path.join(MODEL_DIR, f"{name}.pkl")
    joblib.dump(model, model_path)

    if rmse < best_rmse:
        best_rmse = rmse
        best_model_name = name
        best_model_object = model

print("\n✅ Best Model:", best_model_name)

# =========================================================
# Save Metrics
# =========================================================
metrics_collection.insert_one({
    "timestamp": datetime.now(timezone.utc),
    "results": results,
    "best_model": best_model_name
})

# =========================================================
# MODEL REGISTRY
# =========================================================
latest_model = registry_collection.find_one(sort=[("version", -1)])
next_version = 1 if not latest_model else latest_model["version"] + 1

registry_collection.update_many({}, {"$set": {"is_production": False}})

registry_collection.insert_one({
    "model_name": best_model_name,
    "version": next_version,
    "metrics": results[best_model_name],
    "feature_columns": feature_columns,
    "model_path": f"models/{best_model_name}.pkl",
    "is_production": True,
    "created_at": datetime.now(timezone.utc)
})

print(f"✅ Model Registry Updated — Version {next_version} is now PRODUCTION")

# =========================================================
# SHAP ANALYSIS
# =========================================================
print("Computing SHAP feature importance...")

print("Computing SHAP feature importance...")

# Use TreeExplainer explicitly for tree models
explainer = shap.TreeExplainer(best_model_object)

# Disable strict additivity check (common fix)
shap_values = explainer.shap_values(X_train, check_additivity=False)

# Convert to numpy array (GradientBoosting returns 2D)
shap_values = np.array(shap_values)

# Mean absolute importance
feature_importance = np.abs(shap_values).mean(axis=0)


shap_results = []
for feature, importance in zip(feature_columns, feature_importance):
    shap_results.append({
        "feature": feature,
        "importance": float(importance)
    })

shap_collection.delete_many({})
shap_collection.insert_many(shap_results)

print("✅ SHAP feature importance stored in MongoDB")
print("✅ Training pipeline completed successfully")
