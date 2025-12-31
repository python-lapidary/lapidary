FROM dhi.io/alpine-base:3.22-dev

RUN apk add mise git bash uv --no-cache

# mise builds python from sources, instead use uv to get the binary
RUN uv python install 3.14



RUN \
    echo 'eval "$(mise activate bash)"' >> ~/.bashrc &&\
    mise install
