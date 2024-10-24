# X-Moderator

A machine learning moderation bot for 𝕏 Communities.


### Feature Roadmap

- [ ] x-moderator-api
  - [ ] gRPC Server
  - [ ] REST API (low-priority)
  - [ ] Text Embedding -> Vectors
  - [ ] Bot control
  - [ ] Cache Service
- [ ] x-moderator-bot
  - [ ] gRPC Client
  - [ ] Selenium navigation
  - [ ] X Communities interfacing
- [ ] x-moderator-migrator
  - [ ] Migrate database across schema overlay versions


### Introduction

X-Moderator is split up into two main repos; "core" (this one) and "dash" the dashboard/front-end:

- :file_folder: `x-moderator` - "core" Mono-repo.
  - :scroll: `x-moderator-bot` - Java selenium bot container.
  - :scroll: `x-moderator-api` - Rust gRPC server and REST API server container.
  - :package: `x-moderator-qdrant` - Qdrant vector database container. (bind mount data)
  - :package: `x-moderator-db` - MariaDB relational database container. (bind mount data)
  - :package: `x-moderator-se-hub` - Selenium hub.
  - :package: `x-moderator-se-node` - Selenium dynamic nodes, nodes will be spawned as `x-moderator-se-node-xyz`.
  - :package: `x-moderator-pma` - PHPMyAdmin Web Database Editor container.
  - :package: `x-moderator-nginx` - URL routing and load-balancing.
- :file_folder: [`x-moderator-dash`](https://github.com/x-swe/x-moderator-dash) - "dash" Dashboard Repository
  - :scroll: `x-moderator-dash` - web dashboard.
  - :scroll: `x-moderator-dash-ws` - websocket service.




## Automated Setup

TODO (xdk.sh)




## Manual Setup

The following steps are for setting up a development environment for X-Moderator.

Before you begin, make sure your terminal shell's current directory is set into this project.

Next, for the sake of simplicity, initialize the following variables:

```sh
export XM_NETWORK_NAME="x-moderator-net"
export XM_MARIADB_DB_NAME="x_moderator"

export XM_MARIADB_IMAGE_NAME="mariadb:11.4.1-rc-jammy"
export XM_VALKEY_IMAGE_NAME="valkey/valkey:7.2-alpine3.19"
export XM_QDRANT_IMAGE_NAME="qdrant/qdrant:v1.9.2"
export XM_NGINX_IMAGE_NAME="nginxproxy/nginx-proxy:1.5"
export XM_PMA_IMAGE_NAME="phpmyadmin:5.2.1-apache"
export XM_SELENIUM_HUB_IMAGE_NAME="selenium/hub:4.25.0-20241010"
export XM_SELENIUM_NODE_IMAGE_NAME="selenium/node-docker:4.25.0-20241010"

export XM_MARIADB_CONTAINER_NAME="x-moderator-mariadb"
export XM_VALKEY_CONTAINER_NAME="x-moderator-valkey"
export XM_QDRANT_CONTAINER_NAME="x-moderator-qdrant"
export XM_NGINX_CONTAINER_NAME="x-moderator-nginx"
export XM_PMA_CONTAINER_NAME="x-moderator-pma"
export XM_SELENIUM_HUB_CONTAINER_NAME="x-moderator-se-hub"
export XM_SELENIUM_NODE_CONTAINER_NAME="x-moderator-se-node"
```


### 1. Setup Docker network

Create a Docker network for all of our services to run in:
```sh
docker network create ${XM_NETWORK_NAME}
```

### 2. Set up MariaDB

Copy the default config for mariadb:
```sh
cp mariadb/mariadb_example.cnf mariadb/mariadb.cnf
```

Edit the `mariadb/mariadb.cnf` config if you want.


Generate a random root password:
```sh
export XM_MARIADB_PASSWORD=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 20)
```

Create the container:
```sh
docker run -d \
	--net ${XM_NETWORK_NAME} \
	--name ${XM_MARIADB_CONTAINER_NAME} \
	--hostname ${XM_MARIADB_CONTAINER_NAME} \
	--expose 3306/tcp \
	--env MARIADB_ROOT_PASSWORD=${XM_MARIADB_PASSWORD} \
	--volume "/$(pwd)/mariadb/mariadb.cnf:/etc/mysql/mariadb.cnf:ro" \
	--volume "/$(pwd)/mariadb/data:/var/lib/mysql:z" \
	${XM_MARIADB_IMAGE_NAME}
```

Create the x_moderator DB user:
```sh
docker run --rm --interactive --net ${XM_NETWORK_NAME} ${XM_MARIADB_IMAGE_NAME} sh -c "exec mariadb -h ${XM_MARIADB_CONTAINER_NAME} --user=root --password=${XM_MARIADB_PASSWORD} < /dev/stdin" <<-EOF
CREATE DATABASE x_moderator;
CREATE USER 'x_moderator'@'%' IDENTIFIED BY 'x_m0d3r4t0r';
GRANT ALL PRIVILEGES ON x_moderator.* TO 'x_moderator'@'%';
FLUSH PRIVILEGES;
EOF
```

### 3. Set up Qdrant

Copy the default config for qdrant:
```sh
cp qdrant/qdrant_example.yaml qdrant/qdrant.yaml
```

Edit the `qdrant/qdrant.yaml` config if you want.
- [Qdrant Configuration](https://qdrant.tech/documentation/guides/configuration/)

Create the container:
```sh
docker run -d \
	--net ${XM_NETWORK_NAME} \
	--name ${XM_QDRANT_CONTAINER_NAME} \
	--hostname ${XM_QDRANT_CONTAINER_NAME} \
	--env QDRANT__TELEMETRY_DISABLED="true" \
	--expose 6333-6334/tcp \
	--volume "/$(pwd)/qdrant/qdrant.yaml:/qdrant/config/production.yaml:ro" \
	--volume "/$(pwd)/qdrant/data:/qdrant/storage:z" \
	${XM_QDRANT_IMAGE_NAME}
```

### 4. Run the migrator

The `x-moderator-migrator` tool is a Dockerized Python script that helps traverse between overlay schema versions with ease.

```sh
# Make sure you are in the migrator's project directory
cd migrator/

# Build the docker image
./docker-build.sh

# Run the docker image
./docker-run.sh

# Change back into the root project directory
cd ..
```

### 5. Setup Selenium Grid

```sh
# Change into selenium directory
cd selenium/

# Spin up Selenium Hub
docker run -d \
	--net ${XM_NETWORK_NAME} \
	--name ${XM_SELENIUM_HUB_CONTAINER_NAME} \
	--hostname ${XM_SELENIUM_HUB_CONTAINER_NAME} \
	--expose 4442-4444/tcp \
	--restart always \
	${XM_SELENIUM_HUB_IMAGE_NAME}

# Copy the dynamic grid configuration
cp example_config.toml config.toml

# Spin up dynamic container (this might have issues on Winblows)
# See https://github.com/SeleniumHQ/docker-selenium/blob/trunk/README.md#dynamic-grid
docker run -d \
	--net ${XM_NETWORK_NAME} \
	-e SE_EVENT_BUS_HOST=${XM_SELENIUM_HUB_CONTAINER_NAME} \
	-e SE_EVENT_BUS_PUBLISH_PORT=4442 \
	-e SE_EVENT_BUS_SUBSCRIBE_PORT=4443 \
	-v $(pwd)/config.toml:/opt/selenium/config.toml \
	-v $(pwd)/assets:/opt/selenium/assets \
	-v /var/run/docker.sock:/var/run/docker.sock \
	${XM_SELENIUM_NODE_IMAGE_NAME}
```

### 6. Setup X-Moderator bot

TODO

### Dashboard

TODO

You may navigate to http://localhost:6333/dashboard#/collections to view the collections via the built-in dashboard.

## Production Setup

TODO

