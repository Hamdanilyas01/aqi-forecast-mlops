import os
import joblib
from pymongo import MongoClient
from dotenv import load_dotenv


def load_production_model():
    load_dotenv()

    MONGO_URI = os.getenv("MONGO_URI")
    client = MongoClient(MONGO_URI)
    db = client["aqi_project"]

    registry_collection = db["model_registry"]

    # Find production model
    production_model = registry_collection.find_one(
        {"is_production": True}
    )

    if not production_model:
        raise Exception("No production model found in registry.")

    model_path = production_model["model_path"]
    feature_columns = production_model["feature_columns"]

    # Build absolute path
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_model_path = os.path.join(BASE_DIR, model_path)

    model = joblib.load(full_model_path)

    print(f"✅ Loaded Production Model: {production_model['model_name']}")
    print(f"Version: {production_model['version']}")

    return model, feature_columns
