# CoderDojoChi eco-system

An open-sourced custom Django application for CoderDojoChi.

## First Time

1. Install python, pip, and [nodejs](https://nodejs.org/).

2. Fork project.

3. Clone forked project.
```git clone git@github.com:USERNAME/coderdojochi.git```

4. Go into cloned directory.
```cd coderdojochi```

5. Install virtualenvwrapper.
   ```pip install virtualenvwrapper```

6. Create virtual environment.
   ```mkvirtualenv coderdojochi --no-site-packages```

7. Install npm packages.
   ```npm install``

8. Run ```npm start```.

9. Follow prompts to set up admin account.

10. Navigate to http://localhost:3000

Great success!

## Every other time

Each time you start working fresh you'll need to activate virtualenv and start the django server (via ```npm start```)...

```bash
cd PROJECT_ROOT_FOLDER
workon coderdojochi
npm start
```
