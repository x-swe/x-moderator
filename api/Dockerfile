FROM rust:latest

# Install protoc
RUN apt-get update && apt-get install -y protobuf-compiler

WORKDIR /app

# Set up Rust project dependencies
RUN cargo new --bin x-moderator-api && cd x-moderator-api && cargo fetch

# Set up user permissions
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN addgroup --gid ${GROUP_ID} user && \
    adduser --uid ${USER_ID} --gid ${USER_ID} --disabled-password --gecos "" user && \
    chown -R user:user /app

USER user

# Run the project
CMD ["cargo", "run", "--release"]
