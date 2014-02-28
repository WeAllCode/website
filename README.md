coderdojochi
============

Django Application

To run locally follow these steps...

```bash
easy_install pip
pip install virtualenv
cd ~/Sites
virtualenv dojo-env --no-site-packages
source dojo-env/bin/activate
git clone git@github.com:CoderDojoChi/coderdojochi.git
cd coderdojochi
pip install -r requirements.txt
python manage.py syncdb
```

Follow prompts to set up admin account

```bash
python manage.py runserver
```

Navigate to http://localhost:8000

Great success!

Each time you start working fresh you'll need to activate virtualenv and start the django server...

```bash
cd ~/Sites
source dojo-env/bin/activate
cd coderdojochi
python manage.py runserver
```
