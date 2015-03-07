'use strict';

var gulp = require('gulp'),
    config = require('../config.json');

gulp.task('copy', function() {
    return gulp.src([
            config.img + '/**',
            '.favicon.ico'
        ], {base: '.'})
        .pipe(gulp.dest(config.dist));
});