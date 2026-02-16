from pymongo import MongoClient
from pymongo.server_api import ServerApi
from data_pipeline.fetch_openmeteo import fetch_openmeteo_data
from data_pipeline.feature_engineering import engineer_features
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client["aqi_project"]
collection = db["features"]


def run_pipeline():
    print("Fetching raw data...")
    raw_df = fetch_openmeteo_data()

    print("Engineering features...")
    features_df = engineer_features(raw_df)

    print("Storing in MongoDB...")
    collection.delete_many({})  # avoid duplication
    collection.insert_many(features_df.to_dict("records"))

    print("✅ Feature pipeline completed successfully")


if __name__ == "__main__":
    run_pipeline()
