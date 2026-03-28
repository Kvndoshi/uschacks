#!/bin/bash
set -euo pipefail

# Automated deployment script for Google Cloud Run
echo "Deploying Hivemind to Google Cloud Run..."

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "ERROR: GEMINI_API_KEY environment variable is not set."
    exit 1
fi

gcloud builds submit --config cloudbuild.yaml \
    --substitutions _GEMINI_API_KEY="$GEMINI_API_KEY"

echo "Deployment complete!"
