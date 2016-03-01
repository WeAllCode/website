'use strict';

var gulp = require('gulp');
var shell = require('gulp-shell');

gulp.task('collectstatic', shell.task([
  'python $DIR_SRC/manage.py collectstatic --noinput'
]));
