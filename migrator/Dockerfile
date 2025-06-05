FROM python:3.9-slim
LABEL name="xmod-migrator"
LABEL description="RDB migration tool"
LABEL maintainer="Anthony Waldsmith <me@anthonyw.me>"

# Install dependencies
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        gcc \
        libmariadb-dev \
        mariadb-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd --create-home --shell /bin/bash xmod
USER xmod
WORKDIR /home/xmod

# Create virtual environment
RUN python3 -m venv .venv
ENV PATH="/home/xmod/.venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Mount point for project files
VOLUME /mnt

# Default command
CMD ["python3", "/mnt/migrator.py"]