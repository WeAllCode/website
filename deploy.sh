#!/bin/sh

if [[ "$1" == "staging" ]]; then

    echo "Deploying to staging..." &&
    cd /home/coderdojo/webapps/coderdojochi_staging/coderdojochi &&
    git checkout develop &&
    git pull origin develop

elif [[ "$1" == "production" ]]; then

    echo "Deploying to production..." &&
    cd /home/coderdojo/webapps/coderdojochi/coderdojochi &&
    git checkout master &&
    git pull origin master

else

    echo "Wrong deployment variable. deploy.sh [staging|production]"
    exit

fi

source ../bin/activate &&
pip install -r requirements.txt --exists-action=s &&
((pip list | grep 'South') && pip uninstall -y South) &&
npm prune &&
npm install &&
./node_modules/gulp/bin/gulp.js build &&
python2.7 manage.py makemigrations &&
python2.7 manage.py migrate &&
python2.7 manage.py collectstatic --noinput &&
../apache2/bin/restart
