FROM ghcr.io/astral-sh/uv:alpine

RUN apk add mise git bash git ssh-client-default --no-cache

RUN uv python install 3.10

RUN \
    echo 'eval "$(mise activate bash)"' >> ~/.bashrc &&\
    mise install
