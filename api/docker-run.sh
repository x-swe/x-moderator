#!/bin/bash

# Change directory to the current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"; cd "${DIR}"
SCRIPT="$0"

NETWORK_NAME="x-moderator-net"
IMAGE_NAME="x-moderator-api"

# Check if the Docker image exists
if ! docker image inspect "${IMAGE_NAME}" &> /dev/null; then
    echo "Docker image ${IMAGE_NAME} does not exist. Building ..."
    docker build -t "${IMAGE_NAME}" .
fi

INTERACTIVE_FLAG="-it"
TEMPORARY_FLAG="--rm"
if [[ "$#" -gt "0" ]]; then
    if [[ "${0}" = "--deploy" ]]; then
        # We actually want to deploy it
        TEMPORARY_FLAG=""
        INTERACTIVE_FLAG=""
    fi
fi

docker run ${TEMPORARY_FLAG} ${INTERACTIVE_FLAG} \
    --name ${IMAGE_NAME} \
    --hostname ${IMAGE_NAME} \
    -u "$(id -u):$(id -g)" \
    --net ${NETWORK_NAME} \
    --volume "/$(pwd):/home/xmoderator/project" \
    --env DB_USERNAME=${DB_USERNAME} \
    --env DB_PASSWORD=${DB_PASSWORD} \
    ${IMAGE_NAME} cargo run $@
