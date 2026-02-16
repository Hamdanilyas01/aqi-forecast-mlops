# from data_pipeline.fetch_openmeteo import fetch_openmeteo_data
# from data_pipeline.feature_engineering import engineer_features

# df = fetch_openmeteo_data()
# df2 = engineer_features(df)

# print(df2.head())
# print(df2.shape)


from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["aqi_project"]
collection = db["features"]

doc = collection.find_one()
print(doc.keys())
