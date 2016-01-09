'use strict';

var gulp = require('gulp');
var shell = require('gulp-shell');

gulp.task('django', shell.task([
    'python $DIR_SRC/manage.py runserver 0.0.0.0:8080'
]));
