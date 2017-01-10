docker build -t "$DOCKER_USER/$DOCKER_REPO:$CIRCLE_BUILD_NUM" .
docker build -t "$DOCKER_USER/$DOCKER_REPO-static:$CIRCLE_BUILD_NUM" ./nginx
