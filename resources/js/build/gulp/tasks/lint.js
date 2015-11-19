'use strict';

var gulp = require('gulp'),
    config = require('../config.json'),
    jshint = require('gulp-jshint'),
    handleErrors = require('../utils/handle-errors');

gulp.task('lint', function() {
    return gulp.src([
            config.js + '/*.js',
            '!' + config.js + '/vendor/*.js',
            '!' + config.js + '/*.min.js'
        ])
        .pipe(jshint('.jshintrc'))
        .pipe(jshint.reporter('jshint-stylish'))
        .pipe(jshint.reporter('fail'))
        .on('error', handleErrors);
});