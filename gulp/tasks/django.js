'use strict';

var gulp = require('gulp'),
    shell = require('gulp-shell');

gulp.task('django', shell.task([
    'python manage.py runserver 0.0.0.0:8000'
]));