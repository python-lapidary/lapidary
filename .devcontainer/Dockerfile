FROM ghcr.io/astral-sh/uv:alpine

RUN apk add mise git bash --no-cache

RUN uv python install 3.14

RUN \
    echo 'eval "$(mise activate bash)"' >> ~/.bashrc &&\
    mise install
