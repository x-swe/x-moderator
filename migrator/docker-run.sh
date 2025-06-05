#!/bin/sh
set -e

# Load defaults from docker-config.sh
CONFIG_SCRIPT="$(dirname "$0")/docker-config.sh"
if [ ! -f "$CONFIG_SCRIPT" ]; then
    echo "Error: $CONFIG_SCRIPT not found" >&2
    exit 1
fi
. "$CONFIG_SCRIPT"

# Initialize variables
PUBLISH_PORT=""
MIGRATOR_ARGS=""

# Parse arguments, preserving quoted strings
while [ $# -gt 0 ]; do
    case "$1" in
        --publish-port)
            if [ $# -lt 2 ]; then
                echo "Error: --publish-port requires a value" >&2
                exit 1
            fi
            PUBLISH_PORT="$2"
            shift 2
            ;;
        *)
            # Append argument, preserving quotes
            MIGRATOR_ARGS="$MIGRATOR_ARGS \"$1\""
            shift
            ;;
    esac
done

if [ -n "$PUBLISH_PORT" ]; then
    echo "Note: --publish-port is not applicable for the migrator, ignored" >&2
fi

# Run the migrator container
echo "Running migrator with arguments: $MIGRATOR_ARGS"
# Use sh -c to execute the command with proper argument handling
docker run --rm -it \
    --network "$NETWORK_NAME" \
    -v "$(pwd):/mnt" \
    -w /mnt \
    -e DB_HOST="$DB_HOST" \
    -e DB_PORT="$DB_PORT" \
    -e DB_USER="$DB_USER" \
    -e DB_PASSWORD="$DB_PASSWORD" \
    -e DB_NAME="$DB_NAME" \
    --user xmod \
    "$IMAGE_NAME":latest \
    sh -c "/home/xmod/.venv/bin/python -B /mnt/migrator.py $MIGRATOR_ARGS"

echo "Migrator execution completed!"
