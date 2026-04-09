import json
import os
from decimal import Decimal
import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "SmartSiteGuardEvents")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def clean(obj):
    if isinstance(obj, list):
        return [clean(x) for x in obj]
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def convert_number(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: convert_number(v) for k, v in value.items()}
    if isinstance(value, list):
        return [convert_number(v) for v in value]
    return value


def normalize_payload(item):
    return {k: convert_number(v) for k, v in item.items()}


def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
        },
        "body": json.dumps(body)
    }


def save_event(payload):
    item = normalize_payload(payload)
    table.put_item(Item=item)


def lambda_handler(event, context):
    if event.get("httpMethod"):
        method = event["httpMethod"]
        if method == "OPTIONS":
            return response(200, {"message": "ok"})

        if method == "POST":
            try:
                body = event.get("body", "{}")
                payload = json.loads(body) if isinstance(body, str) else body
                save_event(payload)
                return response(200, {"message": "Event stored", "event_id": payload.get("event_id")})
            except Exception as e:
                return response(500, {"error": str(e)})

        if method == "GET":
            try:
                result = table.scan(Limit=100)
                return response(200, {"items": clean(result.get("Items", []))})
            except Exception as e:
                return response(500, {"error": str(e)})

        return response(405, {"error": "Method not allowed"})

    if isinstance(event, dict) and event.get("sensor_type"):
        try:
            save_event(event)
            return {"message": "Event stored", "event_id": event.get("event_id")}
        except Exception as e:
            return {"error": str(e)}

    return response(400, {"error": "Invalid event payload"})