import json
import uuid
import os
import time
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
from awscrt import io, mqtt, auth
from awsiot import mqtt_connection_builder
from decimal import Decimal

from rules import classify_event

REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1").strip()
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "SmartSiteGuardEvents").strip()
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "").strip()
IOT_RAW_TOPIC = os.getenv("IOT_TOPIC_RAW", "smartsite/raw").strip()
IOT_PROCESSED_TOPIC = os.getenv("IOT_TOPIC_PROCESSED", "smartsite/processed").strip()
CLIENT_ID = os.getenv("IOT_CLIENT_ID", f"fog-processor-{uuid.uuid4()}")


dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

iot_client = boto3.client("iot", region_name=REGION)


def discover_iot_endpoint():
    if IOT_ENDPOINT:
        return IOT_ENDPOINT
    response = iot_client.describe_endpoint(endpointType="iot:Data-ATS")
    return response["endpointAddress"]


def validate_aws_setup():
    try:
        sts = boto3.client("sts", region_name=REGION)
        identity = sts.get_caller_identity()
        print("AWS credentials validated for account", identity.get("Account"))
    except ClientError as e:
        print("AWS startup validation failed:", e.response.get("Error", {}).get("Message", str(e)))


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


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def store_processed_event(payload):
    try:
        table.put_item(Item=normalize_payload(payload))
        print("Stored in DynamoDB:", payload["event_id"])
    except Exception as e:
        print("DynamoDB store failed:", str(e))


def build_iot_connection():
    endpoint = discover_iot_endpoint()
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
        endpoint=endpoint,
        client_bootstrap=bootstrap,
        region=REGION,
        credentials_provider=auth.AwsCredentialsProvider.new_default_chain(),
        client_id=CLIENT_ID,
        clean_session=False,
        keep_alive_secs=30,
    )

    mqtt_connection.on_connection_interrupted = on_connection_interrupted
    mqtt_connection.on_connection_resumed = on_connection_resumed
    return mqtt_connection


def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted:", error)


def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed: return_code=", return_code, "session_present=", session_present)


def publish_processed(payload, mqtt_connection):
    message = json.dumps(payload)
    try:
        publish_future, packet_id = mqtt_connection.publish(
            topic=IOT_PROCESSED_TOPIC,
            payload=message,
            qos=mqtt.QoS.AT_LEAST_ONCE,
        )
        publish_future.result()
        print("Published processed event to IoT topic:", IOT_PROCESSED_TOPIC, "packet_id=", packet_id)
    except Exception as e:
        print("Publish failed:", str(e))


def on_raw_message(topic, payload, **kwargs):
    raw = json.loads(payload.decode())
    print("Received raw event on topic", topic, "->", raw)
    sensor_type = raw.get("sensor_type")
    value = raw.get("value")

    severity, message = classify_event(sensor_type, value)

    processed = {
        "event_id": str(uuid.uuid4()),
        "site_id": raw.get("site_id"),
        "zone_id": raw.get("zone_id"),
        "sensor_id": raw.get("sensor_id"),
        "sensor_type": sensor_type,
        "value": value,
        "unit": raw.get("unit"),
        "severity": severity,
        "message": message,
        "sensor_timestamp": raw.get("timestamp"),
        "fog_processed_at": now_iso(),
    }

    print("Processed event:", processed)
    store_processed_event(processed)
    publish_processed(processed, mqtt_connection)


def main():
    validate_aws_setup()

    global mqtt_connection
    mqtt_connection = build_iot_connection()
    connect_future = mqtt_connection.connect()
    connect_future.result()

    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=IOT_RAW_TOPIC,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_raw_message,
    )
    subscribe_future.result()
    print(f"Subscribed to AWS IoT topic: {IOT_RAW_TOPIC} (packet_id={packet_id})")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Disconnecting from AWS IoT...")
        mqtt_connection.disconnect().result()


if __name__ == "__main__":
    main()