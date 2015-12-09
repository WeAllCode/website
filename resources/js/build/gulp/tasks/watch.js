'use strict';

var gulp = require('gulp'),
    browserSync = require('browser-sync'),
    config = require('../config.json');

gulp.task('watch', ['lint'], function() {
    gulp.watch(config.sass.src + '/*.scss', ['sass']);
    gulp.watch(config.sprites.src + '/*-2x/*.png', ['resize-sprites']);
    gulp.watch(config.js.src + '/*.js', browserSync.reload);
    gulp.watch([
        config.js.src + '/*.js',
        '!' + config.js.src + '/vendor/*.js',
        '!' + config.js.src + '/*.min.js'
    ], ['lint']);
});
