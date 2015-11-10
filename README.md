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
   ```npm install```

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


## Example steps for branching and creating a pull request

`git fetch upstream` - pull latest from remote

`git checkout develop` - checks out your local develop branch

`git merge upstream/develop` - merges in the latest develop from remote to your local

`git checkout -b feature/some-feature-name` - creates your new local feature branch

`git status` - check changed files locally (edited)

`git add …` — stage changed files locally

`git commit -m 'some commit message'` - commit locally

`git push` - push to your fork on github

To open the pull request, it is recommended to navigate your browser to github.com:USERNAME/coderdojochi.  From their Github should prompt you to open a pull request from your latest committed branch.  The pull request should open against the develop branch of our main repo's :develop branch.

Please include a logical title and detailed description including any information an admin would need to accept the pull request.