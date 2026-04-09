from dotenv import load_dotenv
from pathlib import Path
import os


def load_root_env():
    root_env = Path(__file__).resolve().parents[1] / ".env"
    if root_env.exists():
        load_dotenv(root_env)
        print(f"Loaded environment from {root_env}")
    else:
        load_dotenv()
        print("Loaded environment from default .env lookup")

load_root_env()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
RAW_TOPIC = os.getenv("RAW_TOPIC", "smartsite/raw")

API_ENDPOINT = os.getenv("API_ENDPOINT", "https://fhdebl9w4j.execute-api.us-east-1.amazonaws.com/prod/events")

THRESHOLDS = {
    "temperature": 40.0,
    "gas": 300.0,
    "noise": 95.0,
    "vibration": 8.0,
    "proximity": 1
}