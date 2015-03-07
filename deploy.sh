#!/bin/sh

if [[ "$1" == "staging" ]]; then

    echo "Deploying to staging..." &&
    cd /home/coderdojo/webapps/coderdojochi_staging/coderdojochi &&
    source ../bin/activate &&
    git checkout develop &&
    git pull origin develop &&
    pip install -r requirements.txt --exists-action=s &&
    ((pip list | grep 'South') && pip uninstall -y South) &&
    npm prune &&
    npm install &&
    ./node_modules/gulp/bin/gulp.js build &&
    python2.7 manage.py makemigrations &&
    python2.7 manage.py migrate &&
    python2.7 manage.py collectstatic --noinput &&
    /home/coderdojo/webapps/coderdojochi_staging/apache2/bin/restart

elif [[ "$1" == "production" ]]; then

    echo "Deploying to production..." &&
    cd /home/coderdojo/webapps/coderdojochi/coderdojochi &&
    source ../bin/activate &&
    git checkout master &&
    git pull origin master &&
    pip install -r requirements.txt --exists-action=s &&
    ((pip list | grep 'South') && pip uninstall -y South) &&
    npm prune &&
    npm install &&
    ./node_modules/gulp/bin/gulp.js build &&
    python2.7 manage.py makemigrations &&
    python2.7 manage.py migrate &&
    python2.7 manage.py collectstatic --noinput &&
    /home/coderdojo/webapps/coderdojochi_staging/apache2/bin/restart

else

    echo "Wrong deployment variable. deploy.sh [staging|production]"

fi
