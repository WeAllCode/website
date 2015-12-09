'use strict';

var gulp = require('gulp');
var config = require('../config.json');
var minifyCSS = require('gulp-minify-css');
var rename = require('gulp-rename');
var handleErrors = require('../utils/handle-errors');

gulp.task('cssmin', function() {
    return gulp.src(config.css.dest + '/cdc.css')
        .pipe(rename('cdc.min.css'))
        .pipe(minifyCSS({
            keepSpecialComments: 0
        }))
        .on('error', handleErrors)
        .pipe(gulp.dest(config.css.dest));
});
