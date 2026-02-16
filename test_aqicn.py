import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("AQICN_TOKEN")

url = f"https://api.waqi.info/feed/Lahore/?token={token}"
response = requests.get(url)

print(response.status_code)

data = response.json()

print(data["data"].keys())
