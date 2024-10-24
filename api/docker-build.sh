#!/bin/bash

# Change directory to the current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"; cd "${DIR}"
SCRIPT="$0"

NETWORK_NAME="x-moderator-net"
IMAGE_NAME="x-moderator-api"

# Check if the Docker image exists
if docker image inspect "${IMAGE_NAME}" &> /dev/null; then
    echo -e "Docker image ${IMAGE_NAME} already exists!"
    exit 1
fi

docker build -t "${IMAGE_NAME}" .
