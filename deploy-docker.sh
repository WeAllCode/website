#!/usr/bin/env bash

SHA1=$1
REPONAME=$2
EB_BUCKET=elasticbeanstalk-us-east-1-383928539406

docker push kand/$REPONAME:$SHA1

# Create new Elastic Beanstalk version
DOCKERRUN_FILE=$SHA1-Dockerrun.aws.json
sed "s/<TAG>/$SHA1/; s/<REPO>/$REPONAME/;" < Dockerrun.aws.json.template > $DOCKERRUN_FILE
aws s3 cp $DOCKERRUN_FILE s3://$EB_BUCKET/$DOCKERRUN_FILE

# TODO  : try these with aws commands
eb init -p docker -r us-east-1 coderdojochi
eb create -d coderdojochi-env

aws elasticbeanstalk create-application-version --application-name coderdojochi \
  --version-label $SHA1 --source-bundle S3Bucket=$EB_BUCKET,S3Key=$DOCKERRUN_FILE

# Update Elastic Beanstalk environment to new version
aws elasticbeanstalk update-environment --environment-name coderdojochi-env \
    --version-label $SHA1
