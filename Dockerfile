# Use an official Python runtime as a parent image
FROM python:3.11-alpine

ENV GH_TOKEN=""

RUN apk add --no-cache git

RUN mkdir /ghcli
WORKDIR /ghcli
RUN wget https://github.com/cli/cli/releases/download/v2.73.0/gh_2.73.0_linux_386.tar.gz -O ghcli.tar.gz
RUN tar --strip-components=1 -xf ghcli.tar.gz
RUN ln -s /ghcli/bin/gh /usr/bin/gh

RUN mkdir /app
WORKDIR /app

COPY loader /app/loader
COPY scripts /app/scripts
RUN chmod +x /app/scripts/run-and-open-pr.sh

ENTRYPOINT ["/bin/sh", "/app/scripts/run-and-open-pr.sh"]