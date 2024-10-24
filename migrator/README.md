# x-moderator-migrator

X-Moderator relational database migration tool.

- **docker-build.sh**: Script to build the Docker image.
- **docker-run.sh**: Script to run the Migrator within a docker container interactively.
- **mariadb/**: Directory for MariaDB data.
- **migrations/**: Contains database migration overlay SQL files.
- **venv.sh**: Script to activate the virtual environment (used within the Docker container).

## Quick Start with Docker

For the quickest setup, use Docker. This method ensures all dependencies are isolated and consistent across environments.

### Prerequisites
- Docker installed on your machine.

### Steps:
1. **Build the Docker Image:**
   ```sh
   ./docker-build.sh
   ```

2. **Run the Container:**
   ```sh
   ./docker-run.sh shell
   ```
   This will open an interactive shell inside the container where you can run migration commands.

3. **Perform Migrations:**
   - Use `./docker-run.sh migrate --to-latest` to migrate to the latest version.

## Manual Setup (Discouraged)

> [!WARNING]
> Manual setup involves managing Python versions, dependencies, and environment setup, which can lead to inconsistencies.
> For most users, Docker setup is recommended for simplicity and reliability.

If you must set up manually:

1. **Install Python 3 (Debian):**
   ```sh
   sudo apt-get update
   sudo apt-get install python3 python3-pip
   ```

2. **Create Virtual Environment:**
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Run Migrations:**
   ```sh
   python3 migrator.py migrate --to-latest
   ```
