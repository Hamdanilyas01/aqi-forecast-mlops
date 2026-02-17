from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["test_db"]
db.test.insert_one({"status": "connected"})
print("MongoDB Atlas connected successfully")


# from pymongo import MongoClient
# import os

# client = MongoClient(os.getenv("MONGO_URI"))
# db = client["aqi_project"]
# collection = db["features"]

# print("Total documents:", collection.count_documents({}))

