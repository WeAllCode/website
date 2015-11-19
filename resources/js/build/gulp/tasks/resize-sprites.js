'use strict';

var gulp = require('gulp'),
    config = require('../config.json'),
    del = require('del'),
    imageResize = require('gulp-image-resize'),
    rename = require('gulp-rename'),
    gutil = require('gulp-util');

gulp.task('resize-sprites', function() {
    del([config.dev + config.sprites + '/*-1x'], function(err) {
        gutil.log(gutil.colors.magenta('Removed prior *-1x folders for re-creation of new ones based on *-2x sprites.'));
    });

    gulp.src(config.dev + config.sprites + '/*-2x/*.png')
        .pipe(imageResize({
            width: '50%',
            height: '50%'
        }))
        .pipe(rename(function(path) {
            path.dirname = path.dirname.substring(0, path.dirname.length - 3) + '-1x';
        }))
        .pipe(gulp.dest(config.dev + config.sprites));
});