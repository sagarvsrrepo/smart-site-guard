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
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "smartsite/raw")

SITE_ID = os.getenv("SITE_ID", "site-dublin-01")
ZONE_ID = os.getenv("ZONE_ID", "zone-A")

PUBLISH_INTERVAL_SECONDS = int(os.getenv("PUBLISH_INTERVAL_SECONDS", "2"))

SENSOR_IDS = {
    "temperature": "temp-01",
    "gas": "gas-01",
    "noise": "noise-01",
    "vibration": "vib-01",
    "proximity": "prox-01"
}