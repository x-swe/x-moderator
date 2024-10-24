#!/bin/bash

# Change directory to the current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"; cd "${DIR}"
SCRIPT="$0"

source ./docker-config.sh

# Check if the Docker image exists
if ! docker image inspect "${IMAGE_NAME}" &> /dev/null; then
	echo -e "Run ./docker-build.sh first!"
fi

if [[ "$1" = "shell" ]]; then

	docker run --rm -it \
		-u "$(id -u):$(id -g)" \
		--net ${NETWORK_NAME} \
		--volume "/$(pwd):/home/xmoderator/migrator:z" \
		--env MIGRATOR_DB_USERNAME="x_moderator" \
		--env MIGRATOR_DB_PASSWORD="x_m0d3r4t0r" \
		${IMAGE_NAME} /bin/bash -c "cd migrator/ && /bin/bash"

	exit 0
fi

docker run --rm \
	--name ${IMAGE_NAME} \
	--hostname ${IMAGE_NAME} \
	-u "$(id -u):$(id -g)" \
	--net ${NETWORK_NAME} \
	--volume "/$(pwd):/home/xmoderator/migrator:z" \
	--env MIGRATOR_DB_USERNAME="x_moderator" \
	--env MIGRATOR_DB_PASSWORD="x_m0d3r4t0r" \
	${IMAGE_NAME} /bin/bash ./migrator/venv.sh $@
