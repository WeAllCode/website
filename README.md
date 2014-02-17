coderdojochi
============

Django Application

To run locally follow these steps...

1. $ easy_install pip
2. $ pip install virtualenv
3. $ cd ~/Sites
4. $ virtualenv dojo-env --no-site-packages
5. $ source dojo-env/bin/activate
6. $ git clone git@github.com:CoderDojoChi/coderdojochi.git
7. $ cd coderdojochi
8. $ pip install -r requirements.txt
9. $ python manage.py syncdb
10. Follow prompts to set up admin account
11. $ python manage.py runserver
12. Navigate to http://localhost:8000
13. Great success!

Each time you start working fresh you'll need to activate virtualenv and start the django server...

1. $ cd ~/Sites
2. $ source dojo-env/bin/activate
3. $ cd coderdojochi
4. $ python manage.py runserver
