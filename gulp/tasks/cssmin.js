'use strict';

var gulp = require('gulp'),
    config = require('../config.json'),
    minifyCSS = require('gulp-minify-css'),
    rename = require('gulp-rename'),
    handleErrors = require('../utils/handle-errors');

gulp.task('cssmin', function() {
    return gulp.src(config.css + '/cdc.css')
        .pipe(rename('cdc.min.css'))
        .pipe(minifyCSS({
            keepSpecialComments: 0
        }))
        .on('error', handleErrors)
        .pipe(gulp.dest(config.css));
});
