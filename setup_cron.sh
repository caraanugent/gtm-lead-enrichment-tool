#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH=$(which python3)

# Check required API keys
if [[ -z "$NEWS_API_KEY" || -z "$WALKSCORE_API_KEY" ]]; then
  echo "Missing API keys."
  echo "Please set them before running:"
  echo "export NEWS_API_KEY=your_key"
  echo "export WALKSCORE_API_KEY=your_key"
  exit 1
fi

# Cron job (runs every day at 7 AM)
CRON_JOB="0 7 * * * cd \"$PROJECT_DIR\" && NEWS_API_KEY=\"$NEWS_API_KEY\" WALKSCORE_API_KEY=\"$WALKSCORE_API_KEY\" $PYTHON_PATH main.py >> cron_log.txt 2>&1"

# Install cron job (avoid duplicates)
(crontab -l 2>/dev/null | grep -v 'main.py'; echo "$CRON_JOB") | crontab -

echo "Cron job installed successfully!"
echo "It will run every day at 7:00 AM."