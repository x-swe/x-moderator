#!/bin/sh
set -e

# Change to script's directory
cd "$(dirname "$0")"

# Configuration
CONFIG_SCRIPT="./docker-config.sh"

# Configuration
IMAGE_NAME=${IMAGE_NAME:-xmod-migrator}
TAG="latest"
BUILD_DIR="."

# Check for Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "Error: Docker not installed" >&2
    exit 1
fi

# Build image
echo "Building $IMAGE_NAME:$TAG..."
docker build -t "$IMAGE_NAME:$TAG" "$BUILD_DIR"

echo "Built $IMAGE_NAME:$TAG"