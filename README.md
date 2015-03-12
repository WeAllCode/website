coderdojochi
============

Django Application

To run locally follow these steps...

```bash
git clone git@github.com:CoderDojoChi/coderdojochi.git
cd coderdojochi
pip install virtualenvwrapper
add virtualenv wrapper to your zsh plugins -- list plugins=(virtualenvwrapper) in ~/.zshrc
mkvirtualenv dojo-env --no-site-packages
workon dojo-env
pip install -r requirements.txt
pip uninstall south
python manage.py syncdb
```

Follow prompts to set up admin account

You will need node.js installed for the following steps (http://nodejs.org/)

```bash
npm install
gulp
```

Navigate to http://localhost:8000  (http://localhost:3000 to auto update the browser on css/js changes)

Great success!

Each time you start working fresh you'll need to activate virtualenv and start the django server (via gulp)...

```bash
workon dojo-env
cd ~/Sites/coderdojochi
gulp
```
