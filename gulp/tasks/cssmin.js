'use strict';

var gulp = require('gulp');
var config = require('../config.json');
var cssnano = require('gulp-cssnano');
var rename = require('gulp-rename');
var handleErrors = require('../utils/handle-errors');

gulp.task('cssmin', function() {
    return gulp.src(config.css.dest + '/cdc.css')
        .pipe(rename('cdc.min.css'))
        .pipe(cssnano())
        .pipe(gulp.dest(config.css.dest));
});
