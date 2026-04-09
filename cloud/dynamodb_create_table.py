import boto3

REGION = "us-east-1"
TABLE_NAME = "SmartSiteGuardEvents"

dynamodb = boto3.client("dynamodb", region_name=REGION)

response = dynamodb.create_table(
    TableName=TABLE_NAME,
    AttributeDefinitions=[
        {"AttributeName": "event_id", "AttributeType": "S"},
        {"AttributeName": "fog_processed_at", "AttributeType": "S"}
    ],
    KeySchema=[
        {"AttributeName": "event_id", "KeyType": "HASH"},
        {"AttributeName": "fog_processed_at", "KeyType": "RANGE"}
    ],
    BillingMode="PAY_PER_REQUEST"
)

print(response)