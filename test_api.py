"""
Quick standalone script to verify the API key and connection work,
independent of Streamlit. Useful for debugging without spinning up the app.
"""
import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io/nba/v1"

response = requests.get(
    f"{BASE_URL}/players",
    headers={"Authorization": API_KEY},
    params={"search": "LeBron"}
)

print("Status:", response.status_code)
print(response.json())