#!/usr/bin/env bash

# TODO : START INPUTS
IN_DOCKER_IMAGE_VERSION=$1

BUILD_TMP_DIR=.tmp-deploy
BUILD_DOCKERRUN_TEMPLATE=Dockerrun.aws.json.template

DOCKER_HUB_EMAIL=akos123@gmail.com
DOCKER_HUB_PASS=
DOCKER_HUB_USER=kand
DOCKER_HUB_REPO=coderdojochi
DOCKER_HUB_IMAGE=$DOCKER_HUB_USER/$DOCKER_HUB_REPO:$IN_DOCKER_IMAGE_VERSION

CLI_AWS_ACCESS_KEY=
CLI_AWS_SECRET_ACCESS_KEY=
CLI_AWS_DEFAULT_REGION=us-east-1

AWS_ACCOUNT_ID=
AWS_EB_APP=coderdojochi-test
AWS_EB_APP_ENV=$AWS_EB_APP-env
AWS_EB_BUCKET=elasticbeanstalk-$CLI_AWS_DEFAULT_REGION-$AWS_ACCOUNT_ID
# TODO : END INPUTS

# NOTE :
#   - for docker commands:
#     - need to have a docker machine running
#     - need to have run `eval "$(docker-machine env <machine name>)"`

# TODO : possible to get rid of error message from create? or have skip option
# create environment if one doesn't exist
{
  aws \
    --region $CLI_AWS_DEFAULT_REGION  \
    --cli-connect-timeout 0 \
      elasticbeanstalk create-application \
        --application-name $AWS_EB_APP \
  && echo "Created app '$AWS_EB_APP', continuing..."
} || {
  echo "App '$AWS_EB_APP' exists, continuing..."
}

# setup environment if one doesn't exist
{
  aws \
    --region $CLI_AWS_DEFAULT_REGION \
    --cli-connect-timeout 0 \
      elasticbeanstalk create-environment \
        --application-name $AWS_EB_APP \
        --environment-name $AWS_EB_APP_ENV \
        --solution-stack-name "64bit Amazon Linux 2015.09 v2.0.6 running Multi-container Docker 1.7.1 (Generic)" \
  && echo "Created environment '$AWS_EB_APP_ENV', continuing..."
} || {
  echo "Environment '$AWS_EB_APP_ENV' exists, continuing..."
}

# TODO : ideally this should happen before going to circleci to save some time
# create tagged docker image
docker build -t $DOCKER_HUB_IMAGE .

# push new docker image
docker login -u $DOCKER_HUB_USER -p $DOCKER_HUB_PASS -e $DOCKER_HUB_EMAIL
docker push $DOCKER_HUB_IMAGE

# create new eb version
mkdir -p $BUILD_TMP_DIR
DOCKERRUN_FILE=$IN_DOCKER_IMAGE_VERSION-Dockerrrun.aws.json
sed "s/<IMAGE_USER>/$DOCKER_HUB_USER/; s/<IMAGE_REPO>/$DOCKER_HUB_REPO/; s/<IMAGE_VERSION>/$IN_DOCKER_IMAGE_VERSION/;" < $BUILD_DOCKERRUN_TEMPLATE > $BUILD_TMP_DIR/$DOCKERRUN_FILE && \
  aws s3 cp $BUILD_TMP_DIR/$DOCKERRUN_FILE s3://$AWS_EB_BUCKET/$DOCKERRUN_FILE

# create eb application version
aws \
  --region $CLI_AWS_DEFAULT_REGION \
  --cli-connect-timeout 0 \
    elasticbeanstalk create-application-version \
      --application-name $AWS_EB_APP \
      --version-label $IN_DOCKER_IMAGE_VERSION \
      --source-bundle S3Bucket=$AWS_EB_BUCKET,S3Key=$DOCKERRUN_FILE

# update eb environment to new version
aws \
  --region $CLI_AWS_DEFAULT_REGION \
  --cli-connect-timeout 0 \
    elasticbeanstalk update-environment \
      --environment-name $AWS_EB_APP_ENV \
      --version-label $IN_DOCKER_IMAGE_VERSION

# TODO : clean up temp deploy files
# rm -rf $BUILD_TMP_DIR
docker logout

echo "New version deployed."
