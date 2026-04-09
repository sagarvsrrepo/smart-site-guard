# SmartSite Guard Dashboard and Local Simulator/Fog

This repository contains the local dashboard, fog processor, and simulator code.
It also includes cloud deployment artifacts under `cloud/` and a GitHub Actions workflow for CloudFormation deployment.

This repo contains:
- `dashboard/` — Flask dashboard application
- `fog/` — local fog processor code
- `simulator/` — local simulator code
- `cloud/` — CloudFormation deployment artifacts and PowerShell deploy script
- `.github/workflows/cloud-deploy.yml` — GitHub Actions deploy workflow
- `.env` — local environment values for dashboard and simulator
- `.env.example` — sample environment configuration

## What remains
- Dashboard web application using `dashboard/app.py`
- Local fog processor using `fog/processor.py`
- Local simulator publisher using `simulator/publisher.py`
- Local environment configuration via `.env`

## What was removed
- AWS deployment workflows and CI/CD pipeline files
- Cloud deployment configuration artifacts

## Local run
1. Install dependencies for all components:
   ```bash
   python -m pip install -r dashboard/requirements.txt
   python -m pip install -r fog/requirements.txt
   python -m pip install -r simulator/requirements.txt
   ```

2. Load `.env` values into your shell:
   ```powershell
   cd "e:\Fog edge\project code\SmartSite-Guard"
   Get-Content .env | ForEach-Object {
     if ($_ -and $_ -notmatch '^#') {
       $parts = $_ -split '='; Set-Item -Path env:$($parts[0]) -Value $parts[1]
     }
   }
   ```

3. Run the dashboard:
   ```powershell
   cd dashboard
   python app.py
   ```

4. In separate terminals, run the simulator and fog processor:
   ```powershell
   cd simulator
   python publisher.py
   ```
   ```powershell
   cd fog
   python processor.py
   ```

5. Open `http://localhost:5000`
## Launch all local components

A single helper script is available to start the dashboard, fog processor, and simulator together.

- Bash / Git Bash / WSL:
  ```bash
  chmod +x run_all.sh
  ./run_all.sh
  ```
- PowerShell:
  ```powershell
  .\run_all.ps1
  ```

The scripts load `.env`, start each process, and write logs to `logs/`.
## Required `.env` values
Use the values in the root `.env` file.

- `AWS_DEFAULT_REGION=us-east-1`
- `DYNAMODB_TABLE=SmartSiteGuardEvents`
- `IOT_ENDPOINT=a2cfuddj12dy8q-ats.iot.us-east-1.amazonaws.com`
- `IOT_TOPIC_RAW=smartsite/raw`
- `IOT_TOPIC_PROCESSED=smartsite/processed`
- `SITE_ID=site-dublin-01`
- `ZONE_ID=zone-A`
- `PUBLISH_INTERVAL_SECONDS=2`

## Notes
- The `cloud/` folder now contains the CloudFormation template and `cloud/deploy.ps1` deployment script.
- GitHub Actions deployment is available via `.github/workflows/cloud-deploy.yml`.
- The fog and simulator code is preserved locally for local execution.
- The dashboard reads stored events directly from DynamoDB.

## GitHub Actions deploy secrets
To use the workflow in `.github/workflows/cloud-deploy.yml`, add these repository secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN` (required for temporary learner lab credentials)

The workflow uses the `region` input and defaults to `us-east-1`, so you do not need to store `AWS_REGION` as a secret unless you prefer it.
