# X-Moderator Migrator

The X-Moderator Migrator is a tool for managing relational database schema migrations for the X-Moderator backend.

## Overview

The migrator handles the creation, application, and rollback of database migrations for X-Moderator, ensuring schema consistency across environments. It supports features like dry runs, schema validation, data loss detection, and automatic naming of migrations. The tool integrates with Docker for streamlined setup and execution, leveraging scripts to manage local services (MariaDB, Qdrant, Valkey) for development.

### X-Moderator Database

The database supports three main user privileges:

- **Global Administrators**: Identified by `is_global_admin = 1` in `users`, with site-wide privileges.
- **Administrators**: Identified by `role = 2` in `community_members`, with community-specific admin rights.
- **Moderators**: Identified by `role = 1` in `community_members`, handling moderation tasks within communities.

Bot banning is configurable globally (`settings` with `key = 'bot.enable_banning'`, `community_id = NULL`) and per community (`settings` with `community_id` set), with an `active` flag (`0 = passive`, `1 = active`) to indicate enforcement or default status. Appeals are community-specific, and users can only appeal in communities they are members of, validated via `community_members`.

### Key Files
- **`docker-bootstrap.sh`**: Initializes local services (MariaDB, Qdrant, Valkey) for development.
- **`docker-build.sh`**: Builds the migrator Docker image.
- **`docker-config.sh`**: Configures environment variables for database connectivity.
- **`docker-run.sh`**: Executes the migrator container with specified commands.
- **`migrations/`**: Stores migration directories (`<timestamp>_<name>/`) containing `up.sql` (apply) and `down.sql` (rollback) files.
- **`migrator.py`**: Core migration logic, supporting commands like `--to-latest`, `--new`, and `--dry-run`.
- **`requirements.txt`**: Python dependencies.
- **`venv.sh`**: Activates the virtual environment for manual setups.

## Quick Start with Docker

First run `./docker-bootstrap.sh` to download and/or start the required services (MariaDB, Qdrant, Valkey).

Then run `./docker-build.sh` to build the migrator tool.

### Common Commands
- **List migrations**: `./docker-run.sh --list`
- **Check status of migrations**: `./docker-run.sh --status`
- **Create a new migration schema**: `./docker-run.sh --new`
- **Migrate to latest version**: `./docker-run.sh --to-latest`
- **Migrate to a specific version**: `./docker-run.sh --to <timestamp_or_name>`
- **Dry run of migrating to latest version**: `./docker-run.sh --to-latest --dry-run`
- **Non-interactive**: Add `--ignore-warnings` to bypass data loss prompts.

## Manual Setup (Non-Docker)

For environments without Docker, use Python 3.9+ and pip.

> [!WARNING]
> If you are not using Docker then you cannot use the `./docker-bootstrap.sh` script either,
> which means you must manually setup the two databases (MariaDB, QDrant) and Valkey manually.

### Prerequisites
- Python 3.9+ and pip.
- MariaDB server running.
- MariaDB client libraries:
  - Debian/Ubuntu: `libmariadb-dev`, `mariadb-client`
  - macOS (Homebrew): `mariadb-connector-c`
  - Windows: `MariaDB Connector/C`

### Steps
1. **Install Dependencies**
```sh
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install python3 python3-pip libmariadb-dev mariadb-client
# macOS
brew install python3 mariadb-connector-c
```
   For Windows, install Python and MariaDB Connector/C manually.

2. **Set Up Virtual Environment**
```sh
python3 -m venv .venv
```
   Activate:
   - Linux/macOS: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`

3. **Install Python Dependencies**
```sh
pip install -r requirements.txt
```

4. **Run Migrations**
```sh
./venv.sh --to-latest
```
