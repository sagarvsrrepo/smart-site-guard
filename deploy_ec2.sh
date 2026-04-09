#!/usr/bin/env bash
set -euo pipefail

BASE_DIR=${1:-/home/ec2-user/smartsite-guard}
PYTHON_CMD=${2:-python3}
SERVICE_USER=${3:-ec2-user}
ENV_FILE="$BASE_DIR/ec2.env"
VENV_DIR="$BASE_DIR/.venv"

echo "Deploying SmartSite Guard to $BASE_DIR"

sudo mkdir -p "$BASE_DIR"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$BASE_DIR"
cd "$BASE_DIR"

if [ ! -d "$BASE_DIR/.venv" ]; then
  echo "Creating virtual environment..."
  $PYTHON_CMD -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r cloud/requirements.txt -r dashboard/requirements.txt -r fog/requirements.txt -r simulator/requirements.txt

cat > "$ENV_FILE" <<'EOF'
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
DYNAMODB_TABLE=${DYNAMODB_TABLE:-SmartSiteGuardEvents}
IOT_ENDPOINT=${IOT_ENDPOINT:-}
IOT_TOPIC_RAW=${IOT_TOPIC_RAW:-smartsite/raw}
IOT_TOPIC_PROCESSED=${IOT_TOPIC_PROCESSED:-smartsite/processed}
SITE_ID=${SITE_ID:-site-1}
ZONE_ID=${ZONE_ID:-zone-1}
PUBLISH_INTERVAL_SECONDS=${PUBLISH_INTERVAL_SECONDS:-5}
EOF

sudo chown "$SERVICE_USER:$SERVICE_USER" "$ENV_FILE"
sudo chmod 600 "$ENV_FILE"

function create_service() {
  local name=$1
  local workdir=$2
  local exec_start=$3
  local service_file="/etc/systemd/system/$name.service"

  sudo tee "$service_file" > /dev/null <<EOF
[Unit]
Description=SmartSite Guard $name
After=network.target
Requires=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$workdir
EnvironmentFile=$ENV_FILE
ExecStart=$exec_start
Restart=always
RestartSec=10
StandardOutput=append:$BASE_DIR/logs/$name.log
StandardError=append:$BASE_DIR/logs/$name-error.log

[Install]
WantedBy=multi-user.target
EOF

  sudo systemctl daemon-reload
  sudo systemctl enable "$name.service"
  sudo systemctl restart "$name.service"
}

mkdir -p "$BASE_DIR/logs"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$BASE_DIR/logs"

create_service "smartsite-dashboard" "$BASE_DIR/dashboard" "$VENV_DIR/bin/gunicorn app:application --bind 0.0.0.0:5000"
create_service "smartsite-fog" "$BASE_DIR" "$VENV_DIR/bin/python fog/processor.py"
create_service "smartsite-simulator" "$BASE_DIR" "$VENV_DIR/bin/python simulator/publisher.py"

echo "EC2 deployment completed."
