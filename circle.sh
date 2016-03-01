#!/usr/bin/env bash

DOCKER_EMAIL=ali@karbassi.com
DOCKER_USER=karbassi
DOCKER_PASS=nU5!yVVpTYwtvKh^jQ!d
DOCKER_REPO=coderdojochi

CIRCLE_BUILD_NUM=3

docker login  -e "$DOCKER_EMAIL" -u "$DOCKER_USER" -p "$DOCKER_PASS" https://index.docker.io/v1/
# docker login  -e "$DOCKER_EMAIL" -u "$DOCKER_USER" -p "$DOCKER_PASS"
# docker build -t "$DOCKER_USER/$DOCKER_REPO:$CIRCLE_BUILD_NUM" .
# docker push "$DOCKER_USER/$DOCKER_REPO:$CIRCLE_BUILD_NUM"
# sed -i'' -e "s;%USER%;$DOCKER_USER;g" ./.deploy/Dockerrun.aws.json
# sed -i'' -e "s;%REPO%;$DOCKER_REPO;g" ./.deploy/Dockerrun.aws.json
# sed -i'' -e "s;%BUILD_NUM%;$CIRCLE_BUILD_NUM;g" ./.deploy/Dockerrun.aws.json
# cd ./.deploy
# eb init -p "64bit Amazon Linux 2015.09 v2.0.8 running Multi-container Docker 1.9.1 (Generic)" -r us-east-1 $DOCKER_REPO-test8
# eb create -p "64bit Amazon Linux 2015.09 v2.0.8 running Multi-container Docker 1.9.1 (Generic)" -r us-east-1 -d $DOCKER_REPO-test8
# eb deploy -l $CIRCLE_BUILD_NUM $DOCKER_REPO-test8
