FROM debian:trixie-slim
LABEL name="x-moderator-migrator"
LABEL description="RDB migration tool"
LABEL maintainer="Anthony Waldsmith <awaldsmith@protonmail.com>"

RUN apt-get update -y \
	&& apt-get install -y --no-install-recommends \
		bash \
		gcc \
		git \
		make \
		curl \
		python3-dev \
		python3-venv \
		python3-pip \
		libmariadb-dev \
		mariadb-client \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash xmoderator \
	&& chown -R xmoderator:xmoderator /home/xmoderator

USER xmoderator

WORKDIR /home/xmoderator

RUN python3 -m venv .venv \
	&& . .venv/bin/activate \
	&& pip install mariadb==1.1.7 argparse

VOLUME /home/xmoderator

CMD ["/bin/bash"]
