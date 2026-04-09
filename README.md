# SmartSite Guard Dashboard

SmartSite Guard is now simplified to a dashboard-only AWS deployment.

This repo contains:
- `dashboard/` — Flask dashboard application
- `.github/workflows/eb-deploy.yml` — Elastic Beanstalk CI/CD pipeline
- `.env` — local environment values for dashboard and optional cloud settings

## What remains
- Dashboard web application using `dashboard/app.py`
- Docker-style Elastic Beanstalk deployment via `dashboard/Procfile`
- DynamoDB table for event storage

## What was removed
- Fog processor code
- Simulator code
- EC2 deployment workflow
- unused CloudFormation and edge deployment artifacts

## Local run
1. Install dependencies:
   ```bash
   cd dashboard
   python -m pip install -r requirements.txt
   ```
2. From the repo root, load `.env` values into your shell and run the dashboard:
   ```powershell
   cd "e:\Fog edge\project code\SmartSite-Guard"
   Get-Content .env | ForEach-Object {
     if ($_ -and $_ -notmatch '^#') {
       $parts = $_ -split '='; Set-Item -Path env:$($parts[0]) -Value $parts[1]
     }
   }
   cd dashboard
   python app.py
   ```
3. Open `http://localhost:5000`

## Required `.env` values
Use the values in the root `.env` file. The dashboard loads them automatically.

- `AWS_DEFAULT_REGION=us-east-1`
- `DYNAMODB_TABLE=SmartSiteGuardEvents`
- `IOT_ENDPOINT=a2cfuddj12dy8q-ats.iot.us-east-1.amazonaws.com`
- `IOT_TOPIC_RAW=smartsite/raw`
- `IOT_TOPIC_PROCESSED=smartsite/processed`
- `SITE_ID=site-dublin-01`
- `ZONE_ID=zone-A`
- `PUBLISH_INTERVAL_SECONDS=2`

## Elastic Beanstalk deployment
1. Create an Elastic Beanstalk application and environment.
2. Set environment variables in EB:
   - `AWS_DEFAULT_REGION`
   - `DYNAMODB_TABLE`
   - `IOT_ENDPOINT`
3. Run the workflow from GitHub Actions or deploy from the AWS console.

## GitHub Actions
The EB pipeline lives in `.github/workflows/eb-deploy.yml`.

Required repo secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `EB_APPLICATION_NAME`
- `EB_ENVIRONMENT_NAME`
- `EB_S3_BUCKET`

## Notes
- The dashboard is the only runtime component kept in this repo.
- DynamoDB is still required for data storage.
- IoT topics are preserved as configuration values, but simulator/fog code is removed.

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
