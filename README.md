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


## Branching and creating pull requests

`git fetch upstream` - pull latest from upstream remote

`git checkout develop` - checks out your local develop branch

`git merge upstream/develop` - merges in the latest develop branch from upstream remote to your local repo

`git checkout -b feature/some-feature-name` - creates a new local feature branch (or `bug/some-bug-name`)

`git status` - review local changes

`git add …` — stage changed files locally for commit

`git commit -m 'some commit message'` - commit locally, please include a detailed message

`git push` - push to your fork on github

To open the pull request, it is recommended to navigate your browser to github.com:USERNAME/coderdojochi.  From their Github should prompt you to open a pull request from your latest committed branch.  The pull request should open against the develop branch of our main repo's :develop branch.

Please include a logical title and detailed description including any information an admin would need to accept the pull request.