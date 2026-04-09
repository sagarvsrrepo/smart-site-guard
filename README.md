# SmartSite Guard

SmartSite Guard is a fog-edge safety monitoring system for construction sites. It uses AWS IoT Core for sensor ingestion, a fog processor for local hazard classification, AWS IoT and DynamoDB for cloud storage, and a Flask dashboard for visualization.

## Architecture

- **Simulator / Sensors** publish raw sensor readings to AWS IoT Core on topic `smartsite/raw`.
- **Fog Processor** subscribes to `smartsite/raw`, classifies hazards, stores events in DynamoDB, and publishes processed events to AWS IoT Core topic `smartsite/processed`.
- **Dashboard** reads from DynamoDB and renders the site status and sensor trends.

## Components

- `simulator/publisher.py` � AWS IoT sensor event publisher
- `fog/processor.py` � Fog processor subscribed to AWS IoT raw events
- `cloud/lambda_function.py` � optional Lambda API and ingestion handler
- `dashboard/app.py` � Flask dashboard that reads DynamoDB

## How data flows

1. `simulator/publisher.py` generates raw sensor events and publishes them to AWS IoT Core on `smartsite/raw`.
2. `fog/processor.py` subscribes to the raw IoT topic, classifies each event, stores the processed event in DynamoDB, and publishes a processed message to `smartsite/processed`.
3. `dashboard/app.py` reads filtered DynamoDB events and renders the site status, charts, alerts, and logs.

### Example log flow

- `[simulator] Connected to AWS IoT Core`
- `[simulator] Published raw event to smartsite/raw: {...}`
- `[fog] Received raw event on topic smartsite/raw -> {...}`
- `[fog] Stored in DynamoDB: <event_id>`
- `[fog] Published processed event to IoT topic: smartsite/processed`
- `[dashboard] Dashboard refreshed, 10 events, 2 high, time range 1 hour`

## Deployment Overview

### 1. AWS IoT Setup

1. Create an AWS IoT Core endpoint:
   ```bash
   aws iot describe-endpoint --endpoint-type iot:Data-ATS
   ```
2. Create an IoT policy that permits:
   - `iot:Connect`
   - `iot:Subscribe`
   - `iot:Publish`
   - `iot:Receive`

3. Attach the policy to an IAM role or user whose credentials are used by the simulator and fog processor.

4. Create DynamoDB table:
   - Table name: `SmartSiteGuardEvents`
   - Primary key: `event_id` (String)

Optional: if you want AWS IoT to route processed events through a topic rule instead of using the fog processor's direct DynamoDB write, create an IoT rule for processed events:
   - SQL: `SELECT * FROM 'smartsite/processed'`
   - Action: DynamoDB table `SmartSiteGuardEvents`

### 2. Run the Components

Use the AWS credential chain rather than loading `.env` for AWS credentials.

For the simulator:
```bash
cd simulator
pip install -r requirements.txt
python publisher.py
```

For the fog processor:
```bash
cd fog
pip install -r requirements.txt
python processor.py
```

For the dashboard:
```bash
cd dashboard
pip install -r requirements.txt
python app.py
```

The dashboard supports custom time range filtering and refreshes graphs, alerts, and logs together.

### 3. Environment Variables

Set the following environment variables in your shell or runtime environment:

- `AWS_DEFAULT_REGION` = `us-east-1`
- `DYNAMODB_TABLE` = `SmartSiteGuardEvents`
- `IOT_ENDPOINT` = `<your-iot-endpoint>.amazonaws.com`
- `IOT_TOPIC_RAW` = `smartsite/raw`
- `IOT_TOPIC_PROCESSED` = `smartsite/processed`

Optional simulator/fog variables:
- `SITE_ID`
- `ZONE_ID`
- `PUBLISH_INTERVAL_SECONDS`

## 4. Elastic Beanstalk Deployment (Dashboard)

The Flask dashboard can be deployed to AWS Elastic Beanstalk as a web application. The repository now includes `dashboard/Procfile` and a WSGI-compatible `application` entry point in `dashboard/app.py`.

### What deploys well to EBS
- `dashboard/app.py` as the web frontend for monitoring
- static assets under `dashboard/static`
- dashboard templates under `dashboard/templates`

### What should remain outside EBS
- `simulator/publisher.py` and `fog/processor.py` are edge/worker processes and are not ideal as part of a single EBS web app.
- AWS IoT Core and DynamoDB are managed AWS services and stay in AWS regardless of EBS.

### Deploying the dashboard to Elastic Beanstalk
1. Create an EB application and environment in the AWS console or using the EB CLI.
2. Deploy the `dashboard` folder contents as the application source.
3. Configure environment variables in Elastic Beanstalk:
   - `AWS_DEFAULT_REGION`
   - `DYNAMODB_TABLE`
   - `IOT_ENDPOINT`

### Elastic Beanstalk GitHub Actions
A new GitHub Actions workflow is available at `.github/workflows/eb-deploy.yml`.

Required repository secrets for EB deployment:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `EB_APPLICATION_NAME`
- `EB_ENVIRONMENT_NAME`
- `EB_S3_BUCKET`

The workflow packages the `dashboard` folder, uploads the bundle to S3, creates an Elastic Beanstalk application version, and updates the target EB environment.

### EC2 GitHub Actions Deployment
A second workflow is available at `.github/workflows/ec2-deploy.yml`.
This workflow deploys the full repository to an EC2 instance, installs dependencies, and configures systemd services for:
- `smartsite-dashboard`
- `smartsite-fog`
- `smartsite-simulator`

Required repository secrets for EC2 deployment:
- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_PORT`
- `EC2_SSH_PRIVATE_KEY`
- `AWS_REGION`
- `DYNAMODB_TABLE`
- `IOT_ENDPOINT`
- `IOT_TOPIC_RAW`
- `IOT_TOPIC_PROCESSED`
- `SITE_ID`
- `ZONE_ID`
- `PUBLISH_INTERVAL_SECONDS`

The workflow copies the repository to `/home/${{ secrets.EC2_USER }}/smartsite-guard`, then runs `deploy_ec2.sh` remotely on the EC2 host.

If you want full platform deployment, the recommended architecture is:
- Dashboard on Elastic Beanstalk or EC2
- DynamoDB in AWS
- AWS IoT Core in AWS
- Simulator and fog processor on EC2, ECS, or edge worker services

## 5. AWS CloudFormation Deployment

A ready-to-use CloudFormation template is available in `cloud/template.yaml`.

1. Open a PowerShell terminal in the `cloud` folder.
2. Deploy the stack using the helper script:
   ```powershell
   cd cloud
   .\deploy.ps1 -StackName SmartSiteGuardStack -Region us-east-1
   ```

The CloudFormation stack creates:
- a DynamoDB table for SmartSite Guard events

## 5. GitHub CI/CD Pipeline

A GitHub Actions workflow is added at `.github/workflows/aws-deploy.yml`.

### Pipeline behavior
- runs on every push to `main`
- can also be triggered manually using `workflow_dispatch`
- installs dependencies for the dashboard, fog processor, simulator, and cloud deploy
- validates Python source files with `py_compile`
- deploys the CloudFormation stack using AWS CLI

### Required GitHub secrets
Set these repository secrets in GitHub Settings > Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- optional: `CLOUDFORMATION_STACK_NAME` (defaults to `SmartSiteGuardStack`)

### Notes
- The workflow deploys `cloud/template.yaml` only, which currently creates the DynamoDB table.
- AWS IoT Core connectivity remains runtime-managed by the simulator and fog processor.

## 6. AWS IoT Rule

The deployed template does not create an AWS IoT rule. The fog processor stores processed events directly into DynamoDB and also publishes processed messages to AWS IoT Core.

If your Learner Lab account allows it, you can add an IoT rule separately in the AWS Console or with `aws iot create-topic-rule` to route `smartsite/processed` into DynamoDB.

- Topic: `smartsite/processed`
- SQL: `SELECT * FROM 'smartsite/processed'`
- Action: Write to DynamoDB table `SmartSiteGuardEvents`

## 6. AWS IoT Policy for Simulator and Fog Devices

Create an AWS IoT policy that allows device clients to publish, subscribe, receive, and connect.

### CLI
```bash
aws iot create-policy \
  --policy-name SmartSiteGuardIoTPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "iot:Connect",
          "iot:Publish",
          "iot:Subscribe",
          "iot:Receive"
        ],
        "Resource": [
          "arn:aws:iot:${AWS_REGION}:${AWS_ACCOUNT_ID}:client/*",
          "arn:aws:iot:${AWS_REGION}:${AWS_ACCOUNT_ID}:topic/smartsite/*",
          "arn:aws:iot:${AWS_REGION}:${AWS_ACCOUNT_ID}:topicfilter/smartsite/*"
        ]
      }
    ]
  }'
```

### Policy document
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect",
        "iot:Publish",
        "iot:Subscribe",
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:123456789012:client/*",
        "arn:aws:iot:us-east-1:123456789012:topic/smartsite/*",
        "arn:aws:iot:us-east-1:123456789012:topicfilter/smartsite/*"
      ]
    }
  ]
}
```

Attach this policy to the IoT certificate or IAM principal used by the simulator/fog processor.

## Notes

- The code now uses AWS IoT Core for raw ingestion and fog-edge processing.
- The dashboard reads stored events directly from DynamoDB.
- `cloud/lambda_function.py` can be used to expose an API or ingest messages from IoT rules.
