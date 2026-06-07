#!/usr/bin/env bash
# Start the Carrvo backend API server.
# Run from the backend/ directory after installing requirements.
set -euo pipefail

if [ ! -f .env ]; then
  echo "No .env file found. Copy .env.example and fill in ANTHROPIC_API_KEY."
  exit 1
fi

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
