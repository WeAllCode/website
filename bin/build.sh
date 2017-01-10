docker build -t "$DOCKER_USER/$DOCKER_REPO:$CIRCLE_BUILD_NUM" .
docker build -t "$DOCKER_USER/$DOCKER_REPO:latest" .
docker build -t "$DOCKER_USER/$DOCKER_REPO-static:$CIRCLE_BUILD_NUM" ./nginx
docker build -t "$DOCKER_USER/$DOCKER_REPO-static:latest" ./nginx
