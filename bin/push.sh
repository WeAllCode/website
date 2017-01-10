#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# Push same image twice.
# - commit hash as the tag.
# - 'latest' as the tag.
#
# 'latest' will always refer to the last image that was built, since the next
# time this script is run, it'll get overridden. The commit hash, however, is a
# constant reference to this image.

docker push $DOCKER_USER/$DOCKER_REPO:$CIRCLE_BUILD_NUM
docker push $DOCKER_USER/$DOCKER_REPO:latest

docker push $DOCKER_USER/$DOCKER_REPO-static:$CIRCLE_BUILD_NUM
docker push $DOCKER_USER/$DOCKER_REPO-static:latest
