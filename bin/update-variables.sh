#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

sed -i'' -e "s;<USER>;$DOCKER_USER;g" ./deploy/Dockerrun.aws.json
sed -i'' -e "s;<REPO>;$DOCKER_REPO;g" ./deploy/Dockerrun.aws.json
sed -i'' -e "s;<BUILD_NUM>;$CIRCLE_BUILD_NUM;g" ./deploy/Dockerrun.aws.json

sed -i'' -e "s;<POSTGRES_HOST>;$POSTGRES_HOST;g" ./deploy/.ebextensions/environment.config
sed -i'' -e "s;<POSTGRES_PORT>;$POSTGRES_PORT;g" ./deploy/.ebextensions/environment.config
sed -i'' -e "s;<POSTGRES_DB>;$POSTGRES_DB;g" ./deploy/.ebextensions/environment.config
sed -i'' -e "s;<POSTGRES_USER>;$POSTGRES_USER;g" ./deploy/.ebextensions/environment.config
sed -i'' -e "s;<POSTGRES_PASSWORD>;$POSTGRES_PASSWORD;g" ./deploy/.ebextensions/environment.config
