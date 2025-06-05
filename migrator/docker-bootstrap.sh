#!/bin/sh
set -e

# Configuration
CONFIG_SCRIPT="$(dirname "$0")/docker-config.sh"
SERVICES="mariadb qdrant valkey"
NETWORK_NAME="xmod-net"
MAX_RETRIES=20
RETRY_DELAY=5
VALKEY_MODE="standalone"  # Default to standalone Valkey

# Check config script
if [ ! -f "$CONFIG_SCRIPT" ]; then
    echo "Error: $CONFIG_SCRIPT not found" >&2
    exit 1
fi

# Load environment variables
. "$CONFIG_SCRIPT"

# Check for Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "Error: Docker not installed" >&2
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is not running" >&2
    exit 1
fi

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a container exists
container_exists() {
    docker ps -a --filter "name=^/$1$" --format '{{.Names}}' | grep -q "^$1$"
}

# Function to check network attachment
check_network_attachment() {
    container=$1
    if docker inspect "$container" --format '{{range .NetworkSettings.Networks}}{{.NetworkID}}{{end}}' | grep -q "$(docker network ls -q -f name=$NETWORK_NAME)"; then
        return 0
    else
        return 1
    fi
}

# Function to check and heal network state
check_network_state() {
    if docker network ls --format '{{.Name}}' | grep -q "^$NETWORK_NAME$"; then
        log "Checking state of Docker network: $NETWORK_NAME"
        if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
            log "Network $NETWORK_NAME exists but is in an inconsistent state."
            if [ "$IGNORE_WARNINGS" != "true" ]; then
                log "Warning: Recreating network $NETWORK_NAME will disconnect any attached containers."
                read -p "Proceed? (y/n): " confirm
                if [ "$confirm" != "y" ]; then
                    log "Aborted network recreation"
                    exit 1
                fi
            fi
            log "Removing and recreating network $NETWORK_NAME..."
            docker network rm "$NETWORK_NAME" >/dev/null
            docker network create "$NETWORK_NAME" >/dev/null
            log "Network $NETWORK_NAME recreated"
        else
            log "Network $NETWORK_NAME exists and is usable"
        fi
    else
        log "Creating Docker network: $NETWORK_NAME"
        docker network create "$NETWORK_NAME" >/dev/null
    fi
}

# Function to check if a port is available
port_available() {
    port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to deploy Valkey (standalone or cluster)
deploy_valkey() {
    if [ "$VALKEY_MODE" = "cluster" ]; then
        log "Deploying Valkey cluster with 3 instances..."
        for i in 1 2 3; do
            container_name="xmod-valkey-$i"
            port=$((6378 + i))
            if container_exists "$container_name"; then
                if [ "$REDEPLOY" = "true" ]; then
                    log "Removing existing container $container_name..."
                    docker rm -f "$container_name" >/dev/null
                else
                    if ! docker inspect -f '{{.State.Running}}' "$container_name" | grep -q "true"; then
                        log "Starting stopped container $container_name..."
                        docker start "$container_name" >/dev/null
                    else
                        log "$container_name already exists and is running"
                    fi
                    continue
                fi
            fi
            log "Running Valkey instance $i..."
            docker run -d \
                --name "$container_name" \
                --hostname "$container_name" \
                --network "$NETWORK_NAME" \
                -p $port:6379 \
                valkey/valkey:7.2 --requirepass "xmodsecret" --cluster-enabled yes
        done
        log "Configuring Valkey cluster..."
        docker exec xmod-valkey-1 valkey-cli --cluster create 127.0.0.1:6379 127.0.0.1:6380 127.0.0.1:6381 --cluster-replicas 0 --pass xmodsecret
    else
        container_name="xmod-valkey-1"
        if container_exists "$container_name"; then
            if [ "$REDEPLOY" = "true" ]; then
                log "Removing existing container $container_name..."
                docker rm -f "$container_name" >/dev/null
            else
                if ! docker inspect -f '{{.State.Running}}' "$container_name" | grep -q "true"; then
                    log "Starting stopped container $container_name..."
                    docker start "$container_name" >/dev/null
                else
                    log "$container_name already exists and is running"
                fi
                return
            fi
        fi
        log "Running standalone Valkey..."
        docker run -d \
            --name "$container_name" \
            --hostname "$container_name" \
            --network "$NETWORK_NAME" \
            -p 6379:6379 \
            valkey/valkey:7.2 --requirepass "xmodsecret"
    fi
    log "Valkey deployed in $VALKEY_MODE mode"
}

# Function to deploy a service
deploy_service() {
    service=$1
    container_name="xmod-$service-1"
    ports=""

    case $service in
        mariadb)
            if [ "$PUBLISH_PORTS" = "true" ]; then
                if port_available 3306; then
                    ports="-p 3306:3306"
                else
                    log "Warning: Port 3306 is already in use. Skipping port publishing for MariaDB."
                fi
            fi
            ;;
        qdrant)
            if [ "$PUBLISH_PORTS" = "true" ]; then
                if port_available 6333 && port_available 6334; then
                    ports="-p 6333:6333 -p 6334:6334"
                else
                    log "Warning: Ports 6333 or 6334 are already in use. Skipping port publishing for Qdrant."
                fi
            fi
            ;;
    esac

    if container_exists "$container_name"; then
        if [ "$REDEPLOY" = "true" ]; then
            if [ "$IGNORE_WARNINGS" != "true" ]; then
                log "Warning: Redeploying $container_name will remove existing container and data."
                read -p "Proceed? (y/n): " confirm
                if [ "$confirm" != "y" ]; then
                    log "Aborted redeployment for $container_name"
                    return
                fi
            fi
            log "Removing existing container $container_name..."
            docker rm -f "$container_name" >/dev/null
        else
            if ! docker inspect -f '{{.State.Running}}' "$container_name" | grep -q "true"; then
                log "Starting stopped container $container_name..."
                docker start "$container_name" >/dev/null
            else
                log "$container_name already exists and is running"
            fi
            if ! check_network_attachment "$container_name"; then
                log "Reconnecting $container_name to $NETWORK_NAME..."
                docker network connect "$NETWORK_NAME" "$container_name"
            fi
            if ! check_service_health "$container_name" "$service"; then
                log "Error: $container_name is unhealthy, consider redeploying with --redeploy"
                docker rm -f "$container_name" >/dev/null
                exit 1
            fi
            return
        fi
    fi

    case $service in
        mariadb)
            log "Pulling MariaDB image..."
            docker pull mariadb:latest
            ROOT_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(12))")
            log "Running MariaDB container..."
            docker run -d \
                --name "$container_name" \
                --hostname "$container_name" \
                --network "$NETWORK_NAME" \
                $ports \
                -e MYSQL_ROOT_PASSWORD="$ROOT_PASSWORD" \
                -e MYSQL_DATABASE="$DB_NAME" \
                -e MYSQL_USER="$DB_USER" \
                -e MYSQL_PASSWORD="$DB_PASSWORD" \
                mariadb:latest
            log "Waiting for MariaDB to start..."
            if check_service_health "$container_name" "$service"; then
                log "Granting privileges to $DB_USER..."
                docker exec -i "$container_name" mariadb -u root -p"$ROOT_PASSWORD" <<EOF
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';
FLUSH PRIVILEGES;
EOF
            else
                log "Error: Failed to start $container_name"
                docker logs "$container_name" >&2
                docker rm -f "$container_name" >/dev/null
                exit 1
            fi
            ;;
        qdrant)
            log "Pulling Qdrant image..."
            docker pull qdrant/qdrant:latest
            log "Running Qdrant container..."
            docker run -d \
                --name "$container_name" \
                --hostname "$container_name" \
                --network "$NETWORK_NAME" \
                $ports \
                qdrant/qdrant:latest
            log "Waiting for Qdrant to start..."
            if ! check_service_health "$container_name" "$service"; then
                log "Error: Failed to start $container_name"
                docker logs "$container_name" >&2
                docker rm -f "$container_name" >/dev/null
                exit 1
            fi
            ;;
    esac
    log "$container_name started"
}

# Function to check service health
check_service_health() {
    container=$1
    service=$2
    attempt=1
    while [ $attempt -le $MAX_RETRIES ]; do
        case $service in
            mariadb)
                if docker exec "$container" mariadb -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" >/dev/null 2>&1; then
                    log "$container is healthy for $service"
                    return 0
                fi
                ;;
            qdrant)
                tcp_output=$(docker run --rm --network "$NETWORK_NAME" alpine sh -c "nc -z $container 6333 >/dev/null 2>&1 && echo 'success' || echo 'failure'")
                if [ "$tcp_output" = "success" ]; then
                    http_status=$(docker run --rm --network "$NETWORK_NAME" curlimages/curl curl -s -o /dev/null -w "%{http_code}" http://$container:6333 2>/dev/null)
                    if [ "$http_status" = "200" ]; then
                        log "$container is healthy for $service"
                        return 0
                    else
                        log "Qdrant HTTP check failed, status: $http_status"
                    fi
                else
                    log "Qdrant TCP check failed: $tcp_output"
                fi
                ;;
            valkey)
                if [ "$VALKEY_MODE" = "cluster" ]; then
                    for i in 1 2 3; do
                        container_name="xmod-valkey-$i"
                        if ! docker exec "$container_name" valkey-cli PING | grep -q "PONG"; then
                            log "Valkey instance $i not ready"
                            break
                        fi
                    done
                    log "Valkey cluster is healthy"
                    return 0
                else
                    if docker exec "$container" valkey-cli PING | grep -q "PONG"; then
                        log "$container is healthy for $service"
                        return 0
                    fi
                fi
                ;;
        esac
        log "Attempt $attempt/$MAX_RETRIES: $container not ready for $service, retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
        attempt=$((attempt + 1))
    done
    log "Error: $container failed to become healthy for $service after $MAX_RETRIES attempts"
    return 1
}

# Cleanup on interrupt
cleanup() {
    log "Interrupted, cleaning up..."
    exit 1
}
trap cleanup INT TERM

# Parse arguments
REDEPLOY=false
IGNORE_WARNINGS=false
PUBLISH_PORTS=false
while [ $# -gt 0 ]; do
    case "$1" in
        --redeploy)
            REDEPLOY=true
            ;;
        --ignore-warnings)
            IGNORE_WARNINGS=true
            ;;
        --publish-ports)
            PUBLISH_PORTS=true
            ;;
        --cluster)
            VALKEY_MODE="cluster"
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 [--redeploy] [--ignore-warnings] [--publish-ports] [--cluster]" >&2
            exit 1
            ;;
    esac
    shift
done

# Check and heal network
check_network_state

# Deploy Valkey
deploy_valkey

# Deploy other services
for service in mariadb qdrant; do
    deploy_service "$service"
done

log "Bootstrap completed"