'use strict';

var gulp = require('gulp');
var config = require('../config.json');
var jshint = require('gulp-jshint');
var handleErrors = require('../utils/handle-errors');

gulp.task('lint', function() {
    return gulp.src([
            config.js.src + '/*.js',
            '!' + config.js.src + '/vendor/*.js',
            '!' + config.js.src + '/*.min.js'
        ])
        .pipe(jshint('.jshintrc'))
        .pipe(jshint.reporter('jshint-stylish'))
        .pipe(jshint.reporter('fail'))
        .on('error', handleErrors);
});
