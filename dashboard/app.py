from flask import Flask, render_template, jsonify, request
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
app = Flask(__name__, static_folder="static", template_folder="templates")
application = app

REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1").strip()
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "SmartSiteGuardEvents").strip()
SENSOR_ORDER = ["temperature", "gas", "noise", "vibration"]
SENSOR_UNITS = {
    "temperature": "C",
    "gas": "ppm",
    "noise": "dB",
    "vibration": "mm/s"
}

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)


def clean(obj):
    if isinstance(obj, list):
        return [clean(x) for x in obj]
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def parse_iso(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def clamp_int(raw_value, minimum, maximum, default):
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, value))


def get_all_items():
    response = table.scan()
    items = clean(response.get("Items", []))
    items.sort(key=lambda x: x.get("fog_processed_at", ""), reverse=True)
    return items


def filter_by_minutes(items, minutes):
    if minutes <= 0:
        return items
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    filtered = []
    for item in items:
        ts = parse_iso(item.get("fog_processed_at", ""))
        if ts and ts >= cutoff:
            filtered.append(item)
    return filtered


def filter_by_time_range(items, start_time=None, end_time=None):
    if not start_time and not end_time:
        return items
    filtered = []
    for item in items:
        ts = parse_iso(item.get("fog_processed_at", ""))
        if not ts:
            continue
        if start_time and ts < start_time:
            continue
        if end_time and ts > end_time:
            continue
        filtered.append(item)
    return filtered


def validate_aws_setup():
    try:
        sts = boto3.client("sts", region_name=REGION)
        identity = sts.get_caller_identity()
        print("AWS credentials validated for account", identity.get("Account"))
    except ClientError as e:
        print("AWS startup validation failed:", e.response.get("Error", {}).get("Message", str(e)))


validate_aws_setup()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/dashboard")
def dashboard_data():
    minutes = clamp_int(request.args.get("minutes", 5), 0, 10080, 5)
    severity_filter = request.args.get("severity", "ALL")
    sensor_filter = request.args.get("sensor", "ALL")

    items = get_all_items()

    start_time = request.args.get("start_time")
    end_time = request.args.get("end_time")
    if start_time or end_time:
        start_dt = parse_iso(start_time) if start_time else None
        end_dt = parse_iso(end_time) if end_time else None
        items = filter_by_time_range(items, start_dt, end_dt)
    else:
        items = filter_by_minutes(items, minutes)

    if severity_filter != "ALL":
        items = [x for x in items if x.get("severity") == severity_filter]
    if sensor_filter != "ALL":
        items = [x for x in items if x.get("sensor_type") == sensor_filter]

    if start_time or end_time:
        chart_points = clamp_int(request.args.get("max_points", 180), 30, 400, 180)
    elif minutes <= 15:
        chart_points = 80
    elif minutes <= 60:
        chart_points = 140
    elif minutes <= 24 * 60:
        chart_points = 220
    else:
        chart_points = 320

    summary = {
        "total_events": len(items),
        "critical": sum(1 for x in items if x.get("severity") == "CRITICAL"),
        "high": sum(1 for x in items if x.get("severity") == "HIGH"),
        "medium": sum(1 for x in items if x.get("severity") == "MEDIUM"),
        "low": sum(1 for x in items if x.get("severity") == "LOW"),
    }

    latest_by_sensor = {}
    series = defaultdict(list)

    for item in items:
        sensor = item.get("sensor_type")
        if sensor in SENSOR_ORDER:
            if sensor not in latest_by_sensor:
                latest_by_sensor[sensor] = item
            if len(series[sensor]) < chart_points:
                series[sensor].append(item)

    charts = {
        sensor: {
            "label": sensor.capitalize(),
            "unit": SENSOR_UNITS[sensor],
            "labels": [p.get("fog_processed_at", "") for p in list(reversed(series[sensor]))],
            "values": [p.get("value", 0) for p in list(reversed(series[sensor]))],
        }
        for sensor in SENSOR_ORDER
    }

    sensor_cards = [
        {
            "sensor_type": sensor,
            "value": latest_by_sensor[sensor].get("value"),
            "unit": latest_by_sensor[sensor].get("unit", SENSOR_UNITS[sensor]),
            "severity": latest_by_sensor[sensor].get("severity"),
            "message": latest_by_sensor[sensor].get("message"),
            "time": latest_by_sensor[sensor].get("fog_processed_at"),
        }
        for sensor in SENSOR_ORDER
        if sensor in latest_by_sensor
    ]

    site_status = "SAFE"
    if summary["critical"] > 0:
        site_status = "CRITICAL"
    elif summary["high"] > 0:
        site_status = "WARNING"
    elif summary["medium"] > 0:
        site_status = "CAUTION"

    return jsonify(
        summary=summary,
        site_status=site_status,
        sensor_cards=sensor_cards,
        charts=charts,
        recent_alerts=items,
        recent_logs=items,
        limits={
            "chart_points": chart_points,
        },
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
