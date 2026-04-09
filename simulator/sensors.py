import random
from datetime import datetime, timezone

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def temperature(site_id, zone_id, sensor_id):
    return {
        "sensor_type": "temperature",
        "sensor_id": sensor_id,
        "site_id": site_id,
        "zone_id": zone_id,
        "value": round(random.uniform(18, 52), 2),
        "unit": "C",
        "timestamp": now_iso()
    }

def gas(site_id, zone_id, sensor_id):
    return {
        "sensor_type": "gas",
        "sensor_id": sensor_id,
        "site_id": site_id,
        "zone_id": zone_id,
        "value": round(random.uniform(60, 450), 2),
        "unit": "ppm",
        "timestamp": now_iso()
    }

def noise(site_id, zone_id, sensor_id):
    return {
        "sensor_type": "noise",
        "sensor_id": sensor_id,
        "site_id": site_id,
        "zone_id": zone_id,
        "value": round(random.uniform(45, 120), 2),
        "unit": "dB",
        "timestamp": now_iso()
    }

def vibration(site_id, zone_id, sensor_id):
    return {
        "sensor_type": "vibration",
        "sensor_id": sensor_id,
        "site_id": site_id,
        "zone_id": zone_id,
        "value": round(random.uniform(0.2, 12.0), 2),
        "unit": "mm/s",
        "timestamp": now_iso()
    }

def proximity(site_id, zone_id, sensor_id):
    return {
        "sensor_type": "proximity",
        "sensor_id": sensor_id,
        "site_id": site_id,
        "zone_id": zone_id,
        "value": random.choice([0, 1]),
        "unit": "flag",
        "timestamp": now_iso()
    }