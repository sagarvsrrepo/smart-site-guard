import json
import os
import time
import random
import uuid
from datetime import datetime, timezone
import boto3
from awscrt import io, mqtt, auth
from awsiot import mqtt_connection_builder
from dotenv import load_dotenv
from pathlib import Path


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1").strip()
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "").strip()
IOT_TOPIC_RAW = os.getenv("IOT_TOPIC_RAW", "smartsite/raw").strip()
CLIENT_ID = os.getenv("IOT_CLIENT_ID", f"simulator-{uuid.uuid4()}")
SITE_ID = os.getenv("SITE_ID", "site-dublin-01").strip()
ZONE_ID = os.getenv("ZONE_ID", "zone-A").strip()
PUBLISH_INTERVAL_SECONDS = int(os.getenv("PUBLISH_INTERVAL_SECONDS", "1"))

SENSOR_IDS = {
    "temperature": os.getenv("TEMP_SENSOR_ID", "temp-01"),
    "gas": os.getenv("GAS_SENSOR_ID", "gas-01"),
    "noise": os.getenv("NOISE_SENSOR_ID", "noise-01"),
    "vibration": os.getenv("VIB_SENSOR_ID", "vib-01"),
    "proximity": os.getenv("PROX_SENSOR_ID", "prox-01"),
}


iot_client = boto3.client("iot", region_name=REGION)


def discover_iot_endpoint():
    if IOT_ENDPOINT:
        return IOT_ENDPOINT
    response = iot_client.describe_endpoint(endpointType="iot:Data-ATS")
    return response["endpointAddress"]


def build_mqtt_connection():
    endpoint = discover_iot_endpoint()
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    return mqtt_connection_builder.websockets_with_default_aws_signing(
        endpoint=endpoint,
        client_bootstrap=bootstrap,
        region=REGION,
        credentials_provider=auth.AwsCredentialsProvider.new_default_chain(),
        client_id=CLIENT_ID,
        clean_session=False,
        keep_alive_secs=30,
    )


def create_sensor_event(sensor_type, sensor_id):
    timestamp = datetime.now(timezone.utc).isoformat()

    if sensor_type == "temperature":
        value = round(random.uniform(20, 50), 2)
        unit = "C"
    elif sensor_type == "gas":
        value = round(random.uniform(200, 400), 2)
        unit = "ppm"
    elif sensor_type == "noise":
        value = round(random.uniform(30, 100), 2)
        unit = "dB"
    elif sensor_type == "vibration":
        value = round(random.uniform(0, 10), 2)
        unit = "mm/s"
    elif sensor_type == "proximity":
        value = random.choice([0, 1])
        unit = "boolean"
    else:
        value = 0
        unit = "unknown"

    return {
        "event_id": str(uuid.uuid4()),
        "site_id": SITE_ID,
        "zone_id": ZONE_ID,
        "sensor_id": sensor_id,
        "sensor_type": sensor_type,
        "value": value,
        "unit": unit,
        "timestamp": timestamp,
    }


def main():
    mqtt_connection = build_mqtt_connection()

    print("Connecting to AWS IoT Core...")
    mqtt_connection.connect().result()
    print("Connected to AWS IoT Core")

    sensor_types = ["temperature", "gas", "noise", "vibration", "proximity"]

    try:
        while True:
            for sensor_type in sensor_types:
                sensor_id = SENSOR_IDS[sensor_type]
                event = create_sensor_event(sensor_type, sensor_id)
                message = json.dumps(event)

                publish_future, packet_id = mqtt_connection.publish(
                    topic=IOT_TOPIC_RAW,
                    payload=message,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                )
                publish_future.result()

                print(f"Published raw event to {IOT_TOPIC_RAW}: {event} (packet_id={packet_id})")
            time.sleep(PUBLISH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Disconnecting from AWS IoT Core...")
        mqtt_connection.disconnect().result()


if __name__ == "__main__":
    main()