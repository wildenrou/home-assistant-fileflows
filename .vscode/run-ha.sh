#!/bin/bash

mkdir .data
mkdir .data/custom_components
touch .data/configuration.yaml
chown -R 1000:1000 .data

docker run --rm \
    -p 8123:8123 \
    -p 5678:5678 \
    -v $(pwd)/.data:/config:rw \
    -v $(pwd)/debug_configuration.yaml:/config/configuration.yaml:ro \
    -v $(pwd)/custom_components:/config/custom_components:ro \
    --user 1000:1000 \
    --name homeassistant \
    homeassistant/home-assistant:2024.6.1
