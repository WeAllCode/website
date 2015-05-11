'use strict';

var gulp = require('gulp'),
    browserSync = require('browser-sync'),
    config = require('../config.json');

gulp.task('watch', ['lint'], function() {
    gulp.watch(config.sass + '/**/*.scss', ['sass']);
    gulp.watch(config.sprites + '/*-2x/*.png', ['resize-sprites']);
    gulp.watch(config.js + '/*.js', browserSync.reload);
    gulp.watch([
        config.js + '/*.js',
        '!' + config.js + '/vendor/*.js',
        '!' + config.js + '/*.min.js'
    ], ['lint']);
});